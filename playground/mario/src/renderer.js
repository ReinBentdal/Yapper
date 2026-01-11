// 8-bit style pixel-perfect renderer
export class Renderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        
        // Disable smoothing for crisp pixel art
        this.ctx.imageSmoothingEnabled = false;
        this.ctx.webkitImageSmoothingEnabled = false;
        this.ctx.mozImageSmoothingEnabled = false;
        this.ctx.msImageSmoothingEnabled = false;
    }
    
    clear() {
        // Clear to sky blue background
        this.ctx.fillStyle = '#87CEEB';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    // Draw a simple colored rectangle (placeholder for sprites)
    rect(x, y, width, height, color) {
        this.ctx.fillStyle = color;
        this.ctx.fillRect(Math.floor(x), Math.floor(y), width, height);
    }
    
    // Draw rectangle with black outline
    rectWithBorder(x, y, width, height, color, borderColor = '#000') {
        // Fill
        this.ctx.fillStyle = color;
        this.ctx.fillRect(Math.floor(x), Math.floor(y), width, height);
        
        // Border
        this.ctx.strokeStyle = borderColor;
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(Math.floor(x), Math.floor(y), width, height);
    }
    
    // Draw simple circle (for dots/coins)
    circle(x, y, radius, color) {
        this.ctx.fillStyle = color;
        this.ctx.beginPath();
        this.ctx.arc(Math.floor(x), Math.floor(y), radius, 0, Math.PI * 2);
        this.ctx.fill();
    }
    
    // Text rendering for UI
    text(text, x, y, color = '#FFF', size = '16px') {
        this.ctx.fillStyle = color;
        this.ctx.font = `${size} monospace`;
        this.ctx.fillText(text, x, y);
    }
}