// Three.js scene setup
let scene, camera, renderer, controls;
let snakeMeshes = [];
let foodMesh;
let gridHelper;

// Game variables
const scoreElement = document.getElementById('score');
const highScoreElement = document.getElementById('high-score');
const gameOverElement = document.getElementById('gameOver');
const finalScoreElement = document.getElementById('finalScore');
const startBtn = document.getElementById('startBtn');
const pauseBtn = document.getElementById('pauseBtn');
const resetBtn = document.getElementById('resetBtn');
const gameContainer = document.getElementById('gameContainer');

// Game constants
const GRID_SIZE = 1;
const BOARD_SIZE = 20; // 20x20 grid (X-Z plane)
const BOARD_HEIGHT = 10; // Height dimension for Y axis
const INITIAL_SPEED = 150; // milliseconds

// Game state
let snake = [{ x: 10, y: 5, z: 10 }]; // Start in center of 3D space
let direction = { x: 0, y: 0, z: 0 };
let moveQueue = []; // Queue to store movement commands
let food = {};
let score = 0;
let highScore = localStorage.getItem('snake3dHighScore') || 0;
let gameRunning = false;
let gamePaused = false;
let gameLoop = null;

// Materials
let snakeMaterial, snakeHeadMaterial, foodMaterial, boardMaterial;

// Initialize the 3D scene
function initThreeJS() {
    // Scene setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a1a);
    
    // Camera setup - positioned for better 3D view
    camera = new THREE.PerspectiveCamera(75, 600 / 450, 0.1, 1000);
    camera.position.set(25, 25, 25);
    camera.lookAt(10, 5, 10);
    
    // Renderer setup
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(600, 450);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    gameContainer.appendChild(renderer.domElement);
    
    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(30, 40, 30);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    directionalLight.shadow.camera.near = 0.5;
    directionalLight.shadow.camera.far = 100;
    directionalLight.shadow.camera.left = -25;
    directionalLight.shadow.camera.right = 25;
    directionalLight.shadow.camera.top = 25;
    directionalLight.shadow.camera.bottom = -25;
    scene.add(directionalLight);
    
    // Create materials
    snakeMaterial = new THREE.MeshLambertMaterial({ color: 0x00ff00 });
    snakeHeadMaterial = new THREE.MeshLambertMaterial({ color: 0x00aa00 });
    foodMaterial = new THREE.MeshLambertMaterial({ color: 0xff0000 });
    boardMaterial = new THREE.MeshLambertMaterial({ color: 0x333333 });
    
    // Create game board
    createGameBoard();
    
    // Mouse controls for camera
    setupCameraControls();
}

// Create the 3D game board
function createGameBoard() {
    // Ground plane
    const groundGeometry = new THREE.PlaneGeometry(BOARD_SIZE, BOARD_SIZE);
    const groundMesh = new THREE.Mesh(groundGeometry, boardMaterial);
    groundMesh.rotation.x = -Math.PI / 2;
    groundMesh.position.y = -0.5;
    groundMesh.position.x = BOARD_SIZE / 2 - 0.5;
    groundMesh.position.z = BOARD_SIZE / 2 - 0.5;
    groundMesh.receiveShadow = true;
    scene.add(groundMesh);
    
    // Ceiling plane
    const ceilingGeometry = new THREE.PlaneGeometry(BOARD_SIZE, BOARD_SIZE);
    const ceilingMaterial = new THREE.MeshLambertMaterial({ color: 0x222222, transparent: true, opacity: 0.3 });
    const ceilingMesh = new THREE.Mesh(ceilingGeometry, ceilingMaterial);
    ceilingMesh.rotation.x = Math.PI / 2;
    ceilingMesh.position.y = BOARD_HEIGHT - 0.5;
    ceilingMesh.position.x = BOARD_SIZE / 2 - 0.5;
    ceilingMesh.position.z = BOARD_SIZE / 2 - 0.5;
    scene.add(ceilingMesh);
    
    // Grid helper for visual reference (ground level)
    gridHelper = new THREE.GridHelper(BOARD_SIZE, BOARD_SIZE, 0x666666, 0x444444);
    gridHelper.position.x = BOARD_SIZE / 2 - 0.5;
    gridHelper.position.y = -0.5;
    gridHelper.position.z = BOARD_SIZE / 2 - 0.5;
    scene.add(gridHelper);
    
    // Walls
    createWalls();
    
    // Add some visual grid lines for Y levels
    for (let y = 1; y < BOARD_HEIGHT; y++) {
        const levelGrid = new THREE.GridHelper(BOARD_SIZE, BOARD_SIZE, 0x444444, 0x222222);
        levelGrid.position.x = BOARD_SIZE / 2 - 0.5;
        levelGrid.position.y = y - 0.5;
        levelGrid.position.z = BOARD_SIZE / 2 - 0.5;
        levelGrid.material.opacity = 0.3;
        levelGrid.material.transparent = true;
        scene.add(levelGrid);
    }
}

// Create boundary walls
function createWalls() {
    const wallHeight = BOARD_HEIGHT;
    const wallThickness = 0.2;
    const wallMaterial = new THREE.MeshLambertMaterial({ color: 0x666666, transparent: true, opacity: 0.8 });
    
    // Front wall
    const frontWall = new THREE.Mesh(
        new THREE.BoxGeometry(BOARD_SIZE + wallThickness, wallHeight, wallThickness),
        wallMaterial
    );
    frontWall.position.set(BOARD_SIZE / 2 - 0.5, wallHeight / 2 - 0.5, -wallThickness / 2);
    frontWall.castShadow = true;
    scene.add(frontWall);
    
    // Back wall
    const backWall = new THREE.Mesh(
        new THREE.BoxGeometry(BOARD_SIZE + wallThickness, wallHeight, wallThickness),
        wallMaterial
    );
    backWall.position.set(BOARD_SIZE / 2 - 0.5, wallHeight / 2 - 0.5, BOARD_SIZE - 0.5 + wallThickness / 2);
    backWall.castShadow = true;
    scene.add(backWall);
    
    // Left wall
    const leftWall = new THREE.Mesh(
        new THREE.BoxGeometry(wallThickness, wallHeight, BOARD_SIZE),
        wallMaterial
    );
    leftWall.position.set(-wallThickness / 2, wallHeight / 2 - 0.5, BOARD_SIZE / 2 - 0.5);
    leftWall.castShadow = true;
    scene.add(leftWall);
    
    // Right wall
    const rightWall = new THREE.Mesh(
        new THREE.BoxGeometry(wallThickness, wallHeight, BOARD_SIZE),
        wallMaterial
    );
    rightWall.position.set(BOARD_SIZE - 0.5 + wallThickness / 2, wallHeight / 2 - 0.5, BOARD_SIZE / 2 - 0.5);
    rightWall.castShadow = true;
    scene.add(rightWall);
}

// Setup camera controls
function setupCameraControls() {
    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };
    
    renderer.domElement.addEventListener('mousedown', (e) => {
        isDragging = true;
        previousMousePosition = { x: e.clientX, y: e.clientY };
    });
    
    renderer.domElement.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        
        const deltaMove = {
            x: e.clientX - previousMousePosition.x,
            y: e.clientY - previousMousePosition.y
        };
        
        // Rotate camera around the board center
        const center = new THREE.Vector3(10, 5, 10);
        const spherical = new THREE.Spherical();
        spherical.setFromVector3(camera.position.clone().sub(center));
        
        spherical.theta -= deltaMove.x * 0.01;
        spherical.phi += deltaMove.y * 0.01;
        spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi));
        
        camera.position.setFromSpherical(spherical).add(center);
        camera.lookAt(center);
        
        previousMousePosition = { x: e.clientX, y: e.clientY };
    });
    
    document.addEventListener('mouseup', () => {
        isDragging = false;
    });
    
    // Zoom with mouse wheel
    renderer.domElement.addEventListener('wheel', (e) => {
        const zoomSpeed = 1;
        const center = new THREE.Vector3(10, 5, 10);
        const direction = camera.position.clone().sub(center).normalize();
        
        if (e.deltaY > 0) {
            camera.position.add(direction.multiplyScalar(zoomSpeed));
        } else {
            camera.position.sub(direction.multiplyScalar(zoomSpeed));
        }
        
        // Constrain zoom distance
        const distance = camera.position.distanceTo(center);
        if (distance < 10) {
            camera.position.copy(center.clone().add(direction.multiplyScalar(10)));
        } else if (distance > 100) {
            camera.position.copy(center.clone().add(direction.multiplyScalar(100)));
        }
        
        camera.lookAt(center);
        e.preventDefault();
    });
}

// Create snake segment mesh (now with Y parameter)
function createSnakeSegment(x, y, z, isHead = false) {
    const geometry = new THREE.BoxGeometry(0.8, 0.8, 0.8);
    const material = isHead ? snakeHeadMaterial : snakeMaterial;
    const mesh = new THREE.Mesh(geometry, material);
    
    mesh.position.set(x, y, z);
    mesh.castShadow = true;
    scene.add(mesh);
    
    return mesh;
}

// Create food mesh (now with Y parameter)
function createFood(x, y, z) {
    const geometry = new THREE.SphereGeometry(0.4, 8, 8);
    const mesh = new THREE.Mesh(geometry, foodMaterial);
    
    mesh.position.set(x, y, z);
    mesh.castShadow = true;
    scene.add(mesh);
    
    // Add pulsing animation to food
    const animate = () => {
        if (mesh.parent) {
            mesh.rotation.y += 0.05;
            mesh.rotation.x += 0.02;
            mesh.scale.setScalar(1 + Math.sin(Date.now() * 0.005) * 0.1);
            requestAnimationFrame(animate);
        }
    };
    animate();
    
    return mesh;
}

// Initialize game
function init() {
    initThreeJS();
    highScoreElement.textContent = highScore;
    generateFood();
    updateSnakeVisual();
    setupEventListeners();
    animate3D();
}

// Setup event listeners
function setupEventListeners() {
    // Keyboard controls
    document.addEventListener('keydown', handleKeyPress);
    
    // Button controls
    startBtn.addEventListener('click', startGame);
    pauseBtn.addEventListener('click', togglePause);
    resetBtn.addEventListener('click', resetGame);
}

// Handle keyboard input (now for full 3D movement)
function handleKeyPress(e) {
    if (!gameRunning || gamePaused) return;
    
    const key = e.key.toLowerCase();
    
    // Map keys to 3D direction vectors
    let newDirection = null;
    
    switch (key) {
        case 'arrowup':
        case 'w':
            newDirection = { x: 0, y: 0, z: -GRID_SIZE };
            break;
        case 'arrowdown':
        case 's':
            newDirection = { x: 0, y: 0, z: GRID_SIZE };
            break;
        case 'arrowleft':
        case 'a':
            newDirection = { x: -GRID_SIZE, y: 0, z: 0 };
            break;
        case 'arrowright':
        case 'd':
            newDirection = { x: GRID_SIZE, y: 0, z: 0 };
            break;
        case 'q':
            newDirection = { x: 0, y: GRID_SIZE, z: 0 }; // Move up
            break;
        case 'e':
            newDirection = { x: 0, y: -GRID_SIZE, z: 0 }; // Move down
            break;
        case ' ':
        case 'escape':
            e.preventDefault();
            togglePause();
            return;
    }
    
    // If a valid direction was pressed, add it to the queue
    if (newDirection) {
        queueMovement(newDirection);
    }
}

// Queue movement command with validation (updated for full 3D)
function queueMovement(newDirection) {
    // Don't queue more than 3 movements to prevent excessive queuing
    if (moveQueue.length >= 3) return;
    
    // Get the effective current direction (last queued direction or current direction)
    const currentEffectiveDirection = moveQueue.length > 0 
        ? moveQueue[moveQueue.length - 1] 
        : direction;
    
    // Prevent reverse direction - can't go directly opposite to current/last queued direction
    const isReverseDirection = 
        (newDirection.x !== 0 && newDirection.x === -currentEffectiveDirection.x) ||
        (newDirection.y !== 0 && newDirection.y === -currentEffectiveDirection.y) ||
        (newDirection.z !== 0 && newDirection.z === -currentEffectiveDirection.z);
    
    if (isReverseDirection) return;
    
    // Don't queue the same direction twice in a row
    if (moveQueue.length > 0) {
        const lastQueued = moveQueue[moveQueue.length - 1];
        if (lastQueued.x === newDirection.x && lastQueued.y === newDirection.y && lastQueued.z === newDirection.z) {
            return;
        }
    } else if (direction.x === newDirection.x && direction.y === newDirection.y && direction.z === newDirection.z) {
        return;
    }
    
    // Add valid movement to queue
    moveQueue.push(newDirection);
}

// Process next movement from queue
function processMovementQueue() {
    if (moveQueue.length > 0) {
        direction = moveQueue.shift();
    }
}

// Generate random food position (full 3D coordinates)
function generateFood() {
    let newFood;
    
    do {
        newFood = {
            x: Math.floor(Math.random() * BOARD_SIZE),
            y: Math.floor(Math.random() * BOARD_HEIGHT),
            z: Math.floor(Math.random() * BOARD_SIZE)
        };
    } while (snake.some(segment => segment.x === newFood.x && segment.y === newFood.y && segment.z === newFood.z));
    
    food = newFood;
    
    // Remove old food mesh if it exists
    if (foodMesh) {
        scene.remove(foodMesh);
    }
    
    // Create new food mesh
    foodMesh = createFood(food.x, food.y, food.z);
}

// Update snake visual representation (now with Y coordinate)
function updateSnakeVisual() {
    // Remove all existing snake meshes
    snakeMeshes.forEach(mesh => {
        scene.remove(mesh);
    });
    snakeMeshes = [];
    
    // Create new snake meshes
    snake.forEach((segment, index) => {
        const mesh = createSnakeSegment(segment.x, segment.y, segment.z, index === 0);
        snakeMeshes.push(mesh);
    });
}

// Start the game
function startGame() {
    if (gameRunning) return;
    
    gameRunning = true;
    gamePaused = false;
    direction = { x: GRID_SIZE, y: 0, z: 0 }; // Start moving right
    moveQueue = []; // Clear any queued movements
    
    startBtn.disabled = true;
    pauseBtn.disabled = false;
    resetBtn.disabled = false;
    
    gameLoop = setInterval(update, INITIAL_SPEED);
}

// Toggle pause
function togglePause() {
    if (!gameRunning) return;
    
    gamePaused = !gamePaused;
    
    if (gamePaused) {
        clearInterval(gameLoop);
        pauseBtn.textContent = 'Resume';
    } else {
        gameLoop = setInterval(update, INITIAL_SPEED);
        pauseBtn.textContent = 'Pause';
    }
}

// Reset game
function resetGame() {
    clearInterval(gameLoop);
    
    snake = [{ x: 10, y: 5, z: 10 }];
    direction = { x: 0, y: 0, z: 0 };
    moveQueue = []; // Clear movement queue
    score = 0;
    gameRunning = false;
    gamePaused = false;
    
    scoreElement.textContent = score;
    gameOverElement.style.display = 'none';
    
    startBtn.disabled = false;
    startBtn.textContent = 'Start Game';
    pauseBtn.disabled = true;
    pauseBtn.textContent = 'Pause';
    resetBtn.disabled = true;
    
    generateFood();
    updateSnakeVisual();
}

// Main game update function
function update() {
    // Process next queued movement before moving snake
    processMovementQueue();
    
    moveSnake();
    
    if (checkCollision()) {
        gameOver();
        return;
    }
    
    if (checkFoodCollision()) {
        eatFood();
    }
    
    updateSnakeVisual();
}

// Move snake (updated for full 3D)
function moveSnake() {
    const head = { ...snake[0] };
    head.x += direction.x;
    head.y += direction.y;
    head.z += direction.z;
    
    snake.unshift(head);
    
    // Remove tail if no food was eaten
    if (!checkFoodCollision()) {
        snake.pop();
    }
}

// Check wall and self collision (updated for full 3D)
function checkCollision() {
    const head = snake[0];
    
    // Wall collision (including Y boundaries)
    if (head.x < 0 || head.x >= BOARD_SIZE || 
        head.y < 0 || head.y >= BOARD_HEIGHT ||
        head.z < 0 || head.z >= BOARD_SIZE) {
        return true;
    }
    
    // Self collision (now checking all 3 dimensions)
    for (let i = 1; i < snake.length; i++) {
        if (head.x === snake[i].x && head.y === snake[i].y && head.z === snake[i].z) {
            return true;
        }
    }
    
    return false;
}

// Check food collision (updated for full 3D)
function checkFoodCollision() {
    const head = snake[0];
    return head.x === food.x && head.y === food.y && head.z === food.z;
}

// Handle eating food
function eatFood() {
    score += 10;
    scoreElement.textContent = score;
    
    if (score > highScore) {
        highScore = score;
        highScoreElement.textContent = highScore;
        localStorage.setItem('snake3dHighScore', highScore);
    }
    
    generateFood();
}

// Game over
function gameOver() {
    clearInterval(gameLoop);
    gameRunning = false;
    
    finalScoreElement.textContent = score;
    gameOverElement.style.display = 'block';
    
    startBtn.disabled = false;
    startBtn.textContent = 'Start New Game';
    pauseBtn.disabled = true;
    resetBtn.disabled = true;
}

// 3D rendering loop
function animate3D() {
    requestAnimationFrame(animate3D);
    renderer.render(scene, camera);
}

// Initialize game when page loads
window.addEventListener('load', init);