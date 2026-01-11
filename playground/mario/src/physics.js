// Basic collision detection and physics helpers
export class Physics {
    // Simple AABB (Axis-Aligned Bounding Box) collision detection
    static checkCollision(rect1, rect2) {
        return rect1.x < rect2.x + rect2.width &&
               rect1.x + rect1.width > rect2.x &&
               rect1.y < rect2.y + rect2.height &&
               rect1.y + rect1.height > rect2.y;
    }
    
    // Apply gravity and integrate velocity
    static applyGravity(entity, gravity, deltaTime) {
        entity.velocityY += gravity * deltaTime;
        entity.y += entity.velocityY * deltaTime;
    }
    
    // Apply horizontal movement
    static applyMovement(entity, deltaTime) {
        entity.x += entity.velocityX * deltaTime;
    }
    
    // Keep entity within screen bounds
    static constrainToScreen(entity, screenWidth, screenHeight) {
        // Left/right bounds
        if (entity.x < 0) {
            entity.x = 0;
            entity.velocityX = 0;
        }
        if (entity.x + entity.width > screenWidth) {
            entity.x = screenWidth - entity.width;
            entity.velocityX = 0;
        }
        
        // Bottom bound (top is handled by platforms/jumping logic)
        if (entity.y + entity.height > screenHeight) {
            entity.y = screenHeight - entity.height;
            entity.velocityY = 0;
            entity.onGround = true;
        }
    }
    
    // Simple ground collision (for now, just screen bottom)
    static checkGroundCollision(entity, screenHeight) {
        const groundY = screenHeight - entity.height;
        if (entity.y >= groundY) {
            entity.y = groundY;
            entity.velocityY = 0;
            entity.onGround = true;
            return true;
        }
        entity.onGround = false;
        return false;
    }
    
    // Helper to create collision rectangle from entity
    static getCollisionRect(entity) {
        return {
            x: entity.x,
            y: entity.y,
            width: entity.width,
            height: entity.height
        };
    }
}