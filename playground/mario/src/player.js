import { Physics } from './physics.js';

// Player character with platformer mechanics
export class Player {
    constructor(x, y) {
        // Position and size
        this.x = x;
        this.y = y;
        this.width = 16;
        this.height = 16;
        
        // Physics
        this.velocityX = 0;
        this.velocityY = 0;
        this.onGround = false;
        
        // Movement constants
        this.moveSpeed = 120; // pixels per second
        this.jumpSpeed = 300; // initial jump velocity
        this.gravity = 800;   // downward acceleration
        
        // Shooting
        this.dots = [];
        this.dotSpeed = 400; // pixels per second
        
        // Game state
        this.lives = 3;
        this.invulnerable = false;
        this.invulnerabilityTime = 0;
        this.invulnerabilityDuration = 1.0; // seconds
    }
    
    update(deltaTime, input, screenWidth, screenHeight) {
        // Handle horizontal movement
        this.velocityX = 0;
        if (input.leftPressed) {
            this.velocityX = -this.moveSpeed;
        }
        if (input.rightPressed) {
            this.velocityX = this.moveSpeed;
        }
        
        // Handle jumping
        if (input.upPressed && this.onGround) {
            this.velocityY = -this.jumpSpeed;
            this.onGround = false;
        }
        
        // Handle shooting
        if (input.shootPressed) {
            this.shoot();
        }
        
        // Apply physics
        Physics.applyMovement(this, deltaTime);
        Physics.applyGravity(this, this.gravity, deltaTime);
        Physics.checkGroundCollision(this, screenHeight);
        Physics.constrainToScreen(this, screenWidth, screenHeight);
        
        // Update dots
        this.updateDots(deltaTime, screenWidth, screenHeight);
        
        // Handle invulnerability timer
        if (this.invulnerable) {
            this.invulnerabilityTime -= deltaTime;
            if (this.invulnerabilityTime <= 0) {
                this.invulnerable = false;
            }
        }
    }
    
    shoot() {
        // Create a new dot projectile
        const dot = {
            x: this.x + this.width / 2,
            y: this.y + this.height / 2,
            width: 4,
            height: 4,
            velocityX: this.dotSpeed,
            velocityY: 0
        };
        this.dots.push(dot);
    }
    
    updateDots(deltaTime, screenWidth, screenHeight) {
        // Update all dots
        for (let i = this.dots.length - 1; i >= 0; i--) {
            const dot = this.dots[i];
            dot.x += dot.velocityX * deltaTime;
            
            // Remove dots that go off screen
            if (dot.x > screenWidth || dot.x < 0) {
                this.dots.splice(i, 1);
            }
        }
    }
    
    // Check if player's dots hit an enemy
    checkDotCollisions(enemies) {
        const hits = [];
        
        for (let i = this.dots.length - 1; i >= 0; i--) {
            const dot = this.dots[i];
            const dotRect = Physics.getCollisionRect(dot);
            
            for (let j = 0; j < enemies.length; j++) {
                const enemy = enemies[j];
                const enemyRect = Physics.getCollisionRect(enemy);
                
                if (Physics.checkCollision(dotRect, enemyRect)) {
                    // Remove the dot
                    this.dots.splice(i, 1);
                    // Mark enemy for removal
                    hits.push(j);
                    break;
                }
            }
        }
        
        return hits; // Return indices of hit enemies
    }
    
    // Take damage from enemy collision
    takeDamage() {
        if (!this.invulnerable) {
            this.lives--;
            this.invulnerable = true;
            this.invulnerabilityTime = this.invulnerabilityDuration;
            return true; // Damage taken
        }
        return false; // No damage (invulnerable)
    }
    
    // Move to next screen (triggered when player reaches right edge)
    canMoveToNextScreen(screenWidth) {
        return this.x >= screenWidth - this.width;
    }
    
    // Reset position for new screen
    resetForNewScreen() {
        this.x = 0;
        this.dots = []; // Clear dots when changing screens
    }
    
    render(renderer) {
        // Player color - flash white when invulnerable
        const color = this.invulnerable && Math.floor(this.invulnerabilityTime * 10) % 2 
            ? '#FFF' : '#FF6B6B';
        
        renderer.rectWithBorder(this.x, this.y, this.width, this.height, color);
        
        // Render dots
        this.dots.forEach(dot => {
            renderer.circle(dot.x + dot.width / 2, dot.y + dot.height / 2, 2, '#FFFF00');
        });
    }
}