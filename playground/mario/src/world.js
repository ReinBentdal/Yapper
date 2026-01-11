import { Physics } from './physics.js';

// Individual coin collectible
export class Coin {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.width = 8;
        this.height = 8;
        this.collected = false;
        
        // Simple animation
        this.animTime = 0;
    }
    
    update(deltaTime) {
        this.animTime += deltaTime * 3; // Animation speed
    }
    
    render(renderer) {
        if (!this.collected) {
            // Simple spinning coin effect with color change
            const brightness = Math.sin(this.animTime) * 0.3 + 0.7;
            const color = `hsl(45, 100%, ${brightness * 50 + 50}%)`;
            renderer.circle(this.x + this.width / 2, this.y + this.height / 2, 4, color);
        }
    }
}

// Manages world state, screen transitions, and level data
export class World {
    constructor() {
        this.currentScreen = 0;
        this.coins = [];
        this.totalCoinsCollected = 0;
        
        // Define level data - each screen has enemies and coins
        this.screens = [
            // Screen 0 - Starting area
            {
                enemies: [
                    { x: 200, y: 568, patrolWidth: 150 },
                    { x: 500, y: 568, patrolWidth: 100 }
                ],
                coins: [
                    { x: 100, y: 500 },
                    { x: 300, y: 400 },
                    { x: 600, y: 350 },
                    { x: 750, y: 500 }
                ]
            },
            // Screen 1 - More enemies
            {
                enemies: [
                    { x: 150, y: 568, patrolWidth: 200 },
                    { x: 400, y: 568, patrolWidth: 80 },
                    { x: 650, y: 568, patrolWidth: 120 }
                ],
                coins: [
                    { x: 50, y: 450 },
                    { x: 250, y: 300 },
                    { x: 450, y: 400 },
                    { x: 550, y: 250 },
                    { x: 700, y: 500 }
                ]
            },
            // Screen 2 - Final area
            {
                enemies: [
                    { x: 100, y: 568, patrolWidth: 150 },
                    { x: 350, y: 568, patrolWidth: 100 },
                    { x: 600, y: 568, patrolWidth: 150 }
                ],
                coins: [
                    { x: 80, y: 300 },
                    { x: 200, y: 200 },
                    { x: 400, y: 450 },
                    { x: 500, y: 150 },
                    { x: 650, y: 350 },
                    { x: 750, y: 200 }
                ]
            }
        ];
        
        this.loadCurrentScreen();
    }
    
    loadCurrentScreen() {
        // Clear and load coins for current screen
        this.coins = [];
        const screenData = this.getCurrentScreenData();
        
        if (screenData.coins) {
            screenData.coins.forEach(coinData => {
                this.coins.push(new Coin(coinData.x, coinData.y));
            });
        }
    }
    
    getCurrentScreenData() {
        if (this.currentScreen >= 0 && this.currentScreen < this.screens.length) {
            return this.screens[this.currentScreen];
        }
        return { enemies: [], coins: [] };
    }
    
    // Check if player can move to next screen
    canMoveToNextScreen() {
        return this.currentScreen < this.screens.length - 1;
    }
    
    // Move to next screen
    moveToNextScreen() {
        if (this.canMoveToNextScreen()) {
            this.currentScreen++;
            this.loadCurrentScreen();
            return true;
        }
        return false;
    }
    
    // Check coin collection
    checkCoinCollections(player) {
        const playerRect = Physics.getCollisionRect(player);
        let coinsCollected = 0;
        
        this.coins.forEach(coin => {
            if (!coin.collected) {
                const coinRect = Physics.getCollisionRect(coin);
                if (Physics.checkCollision(playerRect, coinRect)) {
                    coin.collected = true;
                    coinsCollected++;
                    this.totalCoinsCollected++;
                }
            }
        });
        
        return coinsCollected;
    }
    
    update(deltaTime) {
        // Update coin animations
        this.coins.forEach(coin => {
            coin.update(deltaTime);
        });
    }
    
    render(renderer) {
        // Render coins
        this.coins.forEach(coin => {
            coin.render(renderer);
        });
        
        // Simple screen indicator
        renderer.text(`Screen ${this.currentScreen + 1}/${this.screens.length}`, 10, 580, '#FFF', '14px');
    }
    
    // Get current screen number for UI
    getCurrentScreenNumber() {
        return this.currentScreen + 1;
    }
    
    // Get total screens for UI
    getTotalScreens() {
        return this.screens.length;
    }
    
    // Check if game is complete (reached final screen)
    isGameComplete() {
        return this.currentScreen >= this.screens.length - 1;
    }
}