"""
Chat Graph - LangGraph-based conversational analysis with message history.

Single Responsibility: Build and manage a conversational graph that maintains
proper HumanMessage/AIMessage alternation via LangGraph checkpointer.

Unlike the analysis graph (7 parallel agents, single-shot), this graph:
- Maintains multi-turn conversation history automatically
- Uses MessagesState with add_messages reducer
- Sends the image only on the first message (stored in state)
- LLM receives full conversation context on each invocation
"""

import logging
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph

from ...config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
)

logger = logging.getLogger(__name__)

# System prompt for conversational OSINT analysis
CHAT_SYSTEM_PROMPT = """Eres un analista experto en OSINT (Open Source Intelligence) integrado en el sistema WatchDogs Security City.

Tu rol:
- Analizas imágenes y frames de video con precisión forense
- Respondes preguntas de seguimiento sobre imágenes previamente analizadas
- Mantienes contexto de la conversación previa
- Eres directo, preciso y respondes en ESPAÑOL

Reglas:
- Si te preguntan sobre algo que ya analizaste, usa tu conocimiento previo de la conversación
- Si te preguntan sobre algo nuevo en la imagen, obsérvala de nuevo
- Sé específico: colores, posiciones, detalles concretos
- Si no puedes ver algo con claridad, dilo honestamente
- Nunca inventes información que no puedas observar"""


class ChatGraphState(TypedDict):
    """State for the conversational chat graph."""

    messages: Annotated[list[AnyMessage], add_messages]
    image_base64: str
    analysis_summary: str


class ChatGraphBuilder:
    """Builds and manages the conversational LangGraph for chat."""

    def __init__(self, checkpointer: BaseCheckpointSaver | None = None) -> None:
        """
        Initialize the chat graph builder.

        Args:
            checkpointer: LangGraph checkpointer for message persistence.
                Must be the same instance used by the analysis graph
                so thread_id is shared.
        """
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=OPENAI_TEMPERATURE,
            **({"base_url": OPENAI_BASE_URL} if OPENAI_BASE_URL else {}),
        )
        self.checkpointer = checkpointer
        self.graph = self._build_graph()

        logger.info("ChatGraphBuilder initialized with LangGraph MessagesState")

    def _build_graph(self) -> CompiledStateGraph:
        """Build the conversational graph: START -> chat -> END."""
        workflow = StateGraph(ChatGraphState)

        workflow.add_node("chat", self._chat_node)
        workflow.add_edge(START, "chat")
        workflow.add_edge("chat", END)

        return workflow.compile(checkpointer=self.checkpointer)

    def _chat_node(self, state: ChatGraphState) -> dict[str, Any]:
        """
        Process a chat turn: send messages + image to LLM, return response.

        The checkpointer ensures previous messages are already in state.
        We only need to build the multimodal content for the LLM call.

        Args:
            state: Current chat state with message history and image.

        Returns:
            Dict with new AIMessage to append to messages.
        """
        messages = state["messages"]
        image_base64 = state.get("image_base64", "")
        analysis_summary = state.get("analysis_summary", "")

        # Build the LLM message list
        llm_messages: list[AnyMessage] = []

        # System prompt with analysis context
        system_content = CHAT_SYSTEM_PROMPT
        if analysis_summary:
            system_content += (
                f"\n\nResultados del análisis previo de esta imagen:\n{analysis_summary}"
            )

        llm_messages.append(SystemMessage(content=system_content))

        # Process conversation history
        # For the first message, attach the image to the HumanMessage
        # For subsequent messages, the image context is already established
        first_human_seen = False

        for msg in messages:
            if isinstance(msg, HumanMessage) and not first_human_seen and image_base64:
                # First human message: attach image for multimodal context
                first_human_seen = True
                llm_messages.append(
                    HumanMessage(
                        content=[
                            {"type": "text", "text": msg.content},
                            {"type": "image_url", "image_url": {"url": image_base64}},
                        ]
                    )
                )
            else:
                llm_messages.append(msg)

        logger.info(
            "Chat node processing: %s messages (%s with image)",
            len(messages),
            "yes" if image_base64 else "no",
        )

        # Call LLM
        response = self.llm.invoke(llm_messages)

        logger.info("Chat response generated (%s chars)", len(response.content))

        # Return AIMessage — add_messages reducer will append it
        return {"messages": [AIMessage(content=response.content)]}

    def chat(
        self,
        user_message: str,
        image_base64: str = "",
        analysis_summary: str = "",
        thread_id: str = "",
    ) -> str:
        """
        Send a chat message and get a response.

        Args:
            user_message: The user's question/message.
            image_base64: Base64 image (only needed on first call per session).
            analysis_summary: Summary of previous analysis (only needed on first call).
            thread_id: Session thread ID for conversation persistence.

        Returns:
            The assistant's response text.
        """
        config: RunnableConfig = {
            "configurable": {"thread_id": thread_id},
        }

        # Build input state
        input_state: dict[str, Any] = {
            "messages": [HumanMessage(content=user_message)],
        }

        # Only include image/summary if provided (first message in session)
        if image_base64:
            input_state["image_base64"] = image_base64
        if analysis_summary:
            input_state["analysis_summary"] = analysis_summary

        # Invoke graph — checkpointer handles message history
        result = self.graph.invoke(input_state, config=config)

        # Extract the last AI message
        ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
        if ai_messages:
            return str(ai_messages[-1].content)

        return "No se pudo generar una respuesta."

    def get_history(self, thread_id: str) -> list[dict[str, str]]:
        """
        Retrieve conversation history for a thread.

        Args:
            thread_id: The session thread ID.

        Returns:
            List of dicts with 'role' and 'content' keys.
        """
        config: RunnableConfig = {
            "configurable": {"thread_id": thread_id},
        }

        state = self.graph.get_state(config)
        messages = state.values.get("messages", [])

        history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": str(msg.content)})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": str(msg.content)})

        return history
