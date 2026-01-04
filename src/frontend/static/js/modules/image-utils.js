/**
 * Image Utilities Module
 * Handles image processing operations like cropping ROI
 */

export class ImageUtils {
    /**
     * Crop a frame to the specified Region of Interest (ROI)
     * @param {string} frameBase64 - Base64 encoded image
     * @param {Object} roi - ROI coordinates {x, y, width, height}
     * @returns {string|null} - Cropped image as base64 or null if error
     */
    cropROI(frameBase64, roi) {
        if (!frameBase64 || !roi) {
            console.warn('⚠️ cropROI: Missing frame or ROI');
            return null;
        }
        
        try {
            return new Promise((resolve) => {
                const img = new Image();
                
                img.onload = () => {
                    // Create canvas for cropping
                    const canvas = document.createElement('canvas');
                    canvas.width = roi.width;
                    canvas.height = roi.height;
                    
                    const ctx = canvas.getContext('2d');
                    
                    // Draw cropped region
                    ctx.drawImage(
                        img,
                        roi.x, roi.y,           // Source x, y
                        roi.width, roi.height,   // Source width, height
                        0, 0,                    // Dest x, y
                        roi.width, roi.height    // Dest width, height
                    );
                    
                    // Convert to base64
                    const croppedBase64 = canvas.toDataURL('image/png');
                    console.log('✅ ROI cropped:', roi.width, 'x', roi.height);
                    resolve(croppedBase64);
                };
                
                img.onerror = () => {
                    console.error('❌ Failed to load image for cropping');
                    resolve(null);
                };
                
                img.src = frameBase64;
            });
        } catch (error) {
            console.error('❌ Error cropping ROI:', error);
            return null;
        }
    }
    
    /**
     * Get image dimensions from base64
     * @param {string} base64Image - Base64 encoded image
     * @returns {Promise<{width: number, height: number}>}
     */
    async getImageDimensions(base64Image) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
                resolve({ width: img.width, height: img.height });
            };
            img.onerror = () => {
                reject(new Error('Failed to load image'));
            };
            img.src = base64Image;
        });
    }
}
