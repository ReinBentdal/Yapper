import { Physics } from './physics.js';

// Basic enemy with patrol AI
export class Enemy {
    constructor(x, y, patrolWidth = 100) {
        // Position and size
        this.x = x;
        this.y = y;
        this.width = 16;
        this.height = 16;
        
        // Patrol behavior
        this.startX = x;
        this.patrolWidth = patrolWidth;
        this.moveSpeed = 60; // pixels per second
        this.direction = 1; // 1 = right, -1 = left
        
        // Physics
        this.velocityX = this.moveSpeed * this.direction;
        this.velocityY = 0;
        this.gravity = 800;
        this.onGround = false;
    }
    
    update(deltaTime, screenWidth, screenHeight) {
        // Simple patrol AI - turn around at patrol boundaries
        const leftBound = this.startX;
        const rightBound = this.startX + this.patrolWidth;
        
        // Check if we should turn around
        if (this.x <= leftBound && this.direction === -1) {
            this.direction = 1;
            this.velocityX = this.moveSpeed * this.direction;
        } else if (this.x + this.width >= rightBound && this.direction === 1) {
            this.direction = -1;
            this.velocityX = this.moveSpeed * this.direction;
        }
        
        // Apply movement and physics
        Physics.applyMovement(this, deltaTime);
        Physics.applyGravity(this, this.gravity, deltaTime);
        Physics.checkGroundCollision(this, screenHeight);
        
        // Keep within screen bounds (as backup)
        if (this.x < 0) {
            this.x = 0;
            this.direction = 1;
            this.velocityX = this.moveSpeed * this.direction;
        }
        if (this.x + this.width > screenWidth) {
            this.x = screenWidth - this.width;
            this.direction = -1;
            this.velocityX = this.moveSpeed * this.direction;
        }
    }
    
    render(renderer) {
        // Simple red rectangle for enemy
        renderer.rectWithBorder(this.x, this.y, this.width, this.height, '#FF4444');
    }
}

// Manages collection of enemies for a screen
export class EnemyManager {
    constructor() {
        this.enemies = [];
    }
    
    // Spawn enemies for current screen
    spawnEnemies(screenData) {
        this.enemies = [];
        
        if (screenData.enemies) {
            screenData.enemies.forEach(enemyData => {
                const enemy = new Enemy(
                    enemyData.x,
                    enemyData.y,
                    enemyData.patrolWidth || 100
                );
                this.enemies.push(enemy);
            });
        }
    }
    
    update(deltaTime, screenWidth, screenHeight) {
        this.enemies.forEach(enemy => {
            enemy.update(deltaTime, screenWidth, screenHeight);
        });
    }
    
    // Remove enemies at specified indices (for when hit by player dots)
    removeEnemies(indices) {
        // Sort indices in descending order to remove from end first
        indices.sort((a, b) => b - a);
        indices.forEach(index => {
            if (index >= 0 && index < this.enemies.length) {
                this.enemies.splice(index, 1);
            }
        });
    }
    
    // Check collision with player
    checkPlayerCollision(player) {
        const playerRect = Physics.getCollisionRect(player);
        
        for (const enemy of this.enemies) {
            const enemyRect = Physics.getCollisionRect(enemy);
            if (Physics.checkCollision(playerRect, enemyRect)) {
                return true;
            }
        }
        return false;
    }
    
    render(renderer) {
        this.enemies.forEach(enemy => {
            enemy.render(renderer);
        });
    }
    
    getEnemies() {
        return this.enemies;
    }
}