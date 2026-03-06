/**
 * L-2: Lightweight logger module for production console guard.
 *
 * In production, only warnings and errors are emitted.
 * Set  window.__WATCHDOGS_DEBUG__ = true  (e.g. via browser console)
 * to enable verbose console.log / console.debug output.
 *
 * ES module files:
 *   import { log } from './modules/logger.js';
 *
 * Classic (non-module) scripts:
 *   const log = window.__wdLog;
 *
 * API:
 *   log.debug('Verbose detail', data);   // silenced in prod
 *   log.info('Operational info', data);   // silenced in prod
 *   log.warn('Something odd', data);      // always shown
 *   log.error('Failure', err);            // always shown
 */

const _isDebug = () =>
    window.__WATCHDOGS_DEBUG__ === true ||
    document.documentElement.dataset.debug === 'true';

const _noop = () => {};

export const log = {
    /** Verbose detail — silenced in production. */
    get debug() {
        return _isDebug() ? console.debug.bind(console) : _noop;
    },
    /** Informational — silenced in production. */
    get info() {
        return _isDebug() ? console.log.bind(console) : _noop;
    },
    /** Warnings — always emitted. */
    get warn() {
        return console.warn.bind(console);
    },
    /** Errors — always emitted. */
    get error() {
        return console.error.bind(console);
    },
};

// Expose globally for classic (non-module) scripts
window.__wdLog = log;
