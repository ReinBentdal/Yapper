import { Input } from './input.js';
import { Renderer } from './renderer.js';
import { Player } from './player.js';
import { EnemyManager } from './enemies.js';
import { World } from './world.js';

// Main game controller
export class Game {
    constructor() {
        // Get canvas and set up rendering
        this.canvas = document.getElementById('gameCanvas');
        this.renderer = new Renderer(this.canvas);
        
        // Game systems
        this.input = new Input();
        this.player = new Player(32, 500); // Start near left side
        this.enemyManager = new EnemyManager();
        this.world = new World();
        
        // UI elements
        this.livesElement = document.getElementById('lives');
        this.coinsElement = document.getElementById('coins');
        this.screenElement = document.getElementById('screen');
        
        // Game state
        this.gameState = 'playing'; // 'playing', 'paused', 'gameOver', 'complete'
        this.screenWidth = this.canvas.width;
        this.screenHeight = this.canvas.height;
        
        // Fixed timestep for consistent physics
        this.targetFPS = 60;
        this.fixedDeltaTime = 1 / this.targetFPS;
        this.accumulator = 0;
        this.lastTime = 0;
        
        // Initialize first screen
        this.loadCurrentScreen();
        
        // Start game loop
        this.gameLoop = this.gameLoop.bind(this);
        requestAnimationFrame(this.gameLoop);
    }
    
    loadCurrentScreen() {
        // Load enemies for current screen
        this.enemyManager.spawnEnemies(this.world.getCurrentScreenData());
    }
    
    gameLoop(currentTime) {
        // Convert to seconds
        const deltaTime = Math.min((currentTime - this.lastTime) / 1000, 0.1);
        this.lastTime = currentTime;
        
        // Fixed timestep accumulator
        this.accumulator += deltaTime;
        
        // Process fixed timesteps
        while (this.accumulator >= this.fixedDeltaTime) {
            this.update(this.fixedDeltaTime);
            this.accumulator -= this.fixedDeltaTime;
        }
        
        // Render
        this.render();
        
        // Continue loop
        requestAnimationFrame(this.gameLoop);
    }
    
    update(deltaTime) {
        if (this.gameState !== 'playing') return;
        
        // Update all systems
        this.player.update(deltaTime, this.input, this.screenWidth, this.screenHeight);
        this.enemyManager.update(deltaTime, this.screenWidth, this.screenHeight);
        this.world.update(deltaTime);
        
        // Check player-dot vs enemy collisions
        const hitEnemies = this.player.checkDotCollisions(this.enemyManager.getEnemies());
        if (hitEnemies.length > 0) {
            this.enemyManager.removeEnemies(hitEnemies);
        }
        
        // Check player vs enemy collisions
        if (this.enemyManager.checkPlayerCollision(this.player)) {
            if (this.player.takeDamage()) {
                // Player took damage
                if (this.player.lives <= 0) {
                    this.gameState = 'gameOver';
                }
            }
        }
        
        // Check coin collection
        const coinsCollected = this.world.checkCoinCollections(this.player);
        if (coinsCollected > 0) {
            // Coin collection feedback could go here (sound, particles, etc.)
        }
        
        // Check screen transition
        if (this.player.canMoveToNextScreen(this.screenWidth)) {
            if (this.world.canMoveToNextScreen()) {
                // Move to next screen
                this.world.moveToNextScreen();
                this.player.resetForNewScreen();
                this.loadCurrentScreen();
            } else {
                // Game complete!
                this.gameState = 'complete';
            }
        }
        
        // Update UI
        this.updateUI();
        
        // Update input state for next frame
        this.input.update();
    }
    
    render() {
        // Clear screen
        this.renderer.clear();
        
        if (this.gameState === 'playing') {
            // Render game objects
            this.world.render(this.renderer);
            this.enemyManager.render(this.renderer);
            this.player.render(this.renderer);
        } else if (this.gameState === 'gameOver') {
            // Game over screen
            this.renderer.text('GAME OVER', this.screenWidth / 2 - 60, this.screenHeight / 2, '#FF4444', '24px');
            this.renderer.text('Press F5 to restart', this.screenWidth / 2 - 80, this.screenHeight / 2 + 40, '#FFF', '16px');
        } else if (this.gameState === 'complete') {
            // Victory screen
            this.renderer.text('CONGRATULATIONS!', this.screenWidth / 2 - 100, this.screenHeight / 2 - 20, '#44FF44', '24px');
            this.renderer.text('You explored all areas!', this.screenWidth / 2 - 90, this.screenHeight / 2 + 20, '#FFF', '16px');
            this.renderer.text(`Total coins: ${this.world.totalCoinsCollected}`, this.screenWidth / 2 - 70, this.screenHeight / 2 + 60, '#FFFF44', '16px');
        }
    }
    
    updateUI() {
        if (this.livesElement) {
            this.livesElement.textContent = this.player.lives;
        }
        if (this.coinsElement) {
            this.coinsElement.textContent = this.world.totalCoinsCollected;
        }
        if (this.screenElement) {
            this.screenElement.textContent = `${this.world.getCurrentScreenNumber()}/${this.world.getTotalScreens()}`;
        }
    }
    
    cleanup() {
        this.input.cleanup();
    }
}

// Start the game when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new Game();
});