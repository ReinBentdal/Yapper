// Keyboard input handling for retro platformer controls
export class Input {
    constructor() {
        this.keys = {};
        this.prevKeys = {};
        
        // Bind event handlers
        this.handleKeyDown = this.handleKeyDown.bind(this);
        this.handleKeyUp = this.handleKeyUp.bind(this);
        
        // Start listening
        document.addEventListener('keydown', this.handleKeyDown);
        document.addEventListener('keyup', this.handleKeyUp);
    }
    
    handleKeyDown(event) {
        this.keys[event.code] = true;
    }
    
    handleKeyUp(event) {
        this.keys[event.code] = false;
    }
    
    // Check if key is currently held down
    isDown(keyCode) {
        return !!this.keys[keyCode];
    }
    
    // Check if key was just pressed this frame (wasn't down last frame)
    isPressed(keyCode) {
        return !!this.keys[keyCode] && !this.prevKeys[keyCode];
    }
    
    // Update previous frame state - call this at end of game loop
    update() {
        this.prevKeys = { ...this.keys };
    }
    
    // Movement helpers for cleaner code
    get leftPressed() { return this.isDown('ArrowLeft'); }
    get rightPressed() { return this.isDown('ArrowRight'); }
    get upPressed() { return this.isPressed('ArrowUp'); }
    get shootPressed() { return this.isPressed('KeyX'); }
    
    cleanup() {
        document.removeEventListener('keydown', this.handleKeyDown);
        document.removeEventListener('keyup', this.handleKeyUp);
    }
}