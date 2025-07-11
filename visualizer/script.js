// Конфигурация
const HEX_RADIUS = 20;
const HEX_WIDTH = HEX_RADIUS * 2;
const HEX_HEIGHT = Math.sqrt(3) * HEX_RADIUS;

// Цвета для типов гексов
const HEX_COLORS = {
    1: '#8e44ad', // муравейник - фиолетовый
    2: '#fff',    // пустой - белый
    3: '#8B5C2A', // грязь - коричневый
    4: '#ffe600', // кислота - желтый
    5: '#bdbdbd'  // камни - светло серый
};

// Названия типов муравьев
const ANT_TYPES = {
    0: 'Рабочий',
    1: 'Боец',
    2: 'Разведчик'
};

const ANT_COLORS = {
    0: '#ffe600', // рабочий - желтый
    1: '#e74c3c', // боец - красный
    2: '#2ecc40'  // разведчик - зеленый
};

// Названия типов ресурсов
const FOOD_TYPES = {
    1: 'Яблоко',
    2: 'Хлеб',
    3: 'Нектар'
};

const FOOD_COLORS = {
    1: '#3498db', // яблоко - синий
    2: '#3498db', // хлеб - синий
    3: '#3498db'  // нектар - синий
}

// Названия типов гексов
const HEX_TYPES = {
    1: 'Муравейник',
    2: 'Пустой',
    3: 'Грязь',
    4: 'Кислота',
    5: 'Камни'
};

// Элементы DOM
const canvas = document.getElementById('arenaCanvas');
const ctx = canvas.getContext('2d');
const loadingElement = document.getElementById('loading');
const scoreElement = document.getElementById('score');
const statusTextElement = document.getElementById('statusText');
const refreshBtn = document.getElementById('refreshBtn');
const coordinatesElement = document.getElementById('coordinates');
const antsListElement = document.getElementById('antsList');
const enemiesListElement = document.getElementById('enemiesList');
const foodListElement = document.getElementById('foodList');

// Состояние приложения
let arenaData = null;
let canvasWidth = 0;
let canvasHeight = 0;
let offsetX = 0;
let offsetY = 0;
let scale = 1;
let isDragging = false;
let lastX, lastY;

// Загруженные изображения
const images = {
    scout: null,
    soldier: null,
    worker: null,
    enemyScout: null,
    enemySoldier: null,
    enemyWorker: null,
    house: null,
    apple: null,
    bread: null,
    nectar: null
};

// Загрузка изображений
function loadImages() {
    return new Promise((resolve, reject) => {
        const imageUrls = [
            { key: 'scout', url: 'img/scout.png' },
            { key: 'soldier', url: 'img/soldier.png' },
            { key: 'worker', url: 'img/worker.png' },
            { key: 'house', url: 'img/house.png' },
            { key: 'apple', url: 'img/apple.png' },
            { key: 'bread', url: 'img/bread.png' },
            { key: 'nectar', url: 'img/nectar.png' }
        ];

        let loadedCount = 0;

        imageUrls.forEach(item => {
            const img = new Image();
            img.onload = () => {
                images[item.key] = img;

                // Для scout/soldier/worker создаём чб версии для врагов
                if (item.key === 'scout' || item.key === 'soldier' || item.key === 'worker') {
                    const canvas = document.createElement('canvas');
                    canvas.width = img.width;
                    canvas.height = img.height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);

                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    const data = imageData.data;

                    for (let i = 0; i < data.length; i += 4) {
                        const avg = (data[i] + data[i + 1] + data[i + 2]) / 3;
                        data[i] = avg;     // red
                        data[i + 1] = avg; // green
                        data[i + 2] = avg; // blue
                    }

                    ctx.putImageData(imageData, 0, 0);

                    const enemyImg = new Image();
                    enemyImg.src = canvas.toDataURL();
                    images[`enemy${item.key.charAt(0).toUpperCase() + item.key.slice(1)}`] = enemyImg;
                }

                loadedCount++;
                if (loadedCount === imageUrls.length) {
                    resolve();
                }
            };
            img.onerror = () => {
                console.error(`Ошибка загрузки изображения: ${item.url}`);
                reject(`Ошибка загрузки изображения: ${item.url}`);
            };
            img.src = item.url;
        });
    });
}

// Функция для преобразования осевых координат (q, r) в экранные (x, y) с поворотом на 45 градусов
function hexToPixel(q, r) {
    // Поворачиваем координаты на 45 градусов (меняем местами q и r)
    const rotatedQ = r;
    const rotatedR = q;
    
    const x = (rotatedQ * HEX_WIDTH * 0.75) * scale + offsetX;
    const y = (rotatedR * HEX_HEIGHT + rotatedQ * HEX_HEIGHT * 0.5) * scale + offsetY;
    return {x, y};
}

// Функция для рисования гексагона
function drawHexagon(centerX, centerY, fillColor, strokeColor = '#000') {
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
        const angle = Math.PI / 3 * i;
        const x = centerX + HEX_RADIUS * Math.cos(angle) * scale;
        const y = centerY + HEX_RADIUS * Math.sin(angle) * scale;
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    }
    ctx.closePath();
    
    ctx.fillStyle = fillColor;
    ctx.fill();
    
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 1;
    ctx.stroke();
}

// Функция для рисования изображения муравья
function drawAntImage(centerX, centerY, type, isEnemy = false) {
    let img;
    const size = HEX_RADIUS * 1.5 * scale;

    switch(type) {
        case 0: img = isEnemy ? images.enemyWorker : images.worker; break;
        case 1: img = isEnemy ? images.enemySoldier : images.soldier; break;
        case 2: img = isEnemy ? images.enemyScout : images.scout; break;
        default: img = isEnemy ? images.enemyWorker : images.worker;
    }

    if (img) {
        ctx.drawImage(img, centerX - size/2, centerY - size/2, size, size);
    } else {
        // Если изображение не загружено, fallback цвет
        drawObject(centerX, centerY, isEnemy ? ENEMY_COLOR : ANT_COLORS[type] || '#2196f3', HEX_RADIUS * 0.7, type);
    }
    
    // Отображаем здоровье
    ctx.fillStyle = '#fff';
    ctx.font = `${10 * scale}px Arial`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
}

// Функция для рисования объекта (еда)
function drawObject(centerX, centerY, color, radius, label = '') {
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius * scale, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1;
    ctx.stroke();
    
    if (label) {
        ctx.font = `${10 * scale}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#000';
        ctx.fillStyle = '#fff';
        ctx.strokeText(label, centerX, centerY);
        ctx.fillText(label, centerX, centerY);
    }
}

// Функция для обновления визуализации
function drawArena() {
    if (!arenaData) return;

    ctx.clearRect(0, 0, canvasWidth, canvasHeight);

    // Рисуем все гексы карты
    arenaData.map.forEach(hex => {
        const {x, y} = hexToPixel(hex.q, hex.r);
        const isHome = arenaData.home.some(home => home.q === hex.q && home.r === hex.r);
        const color = isHome ? HEX_COLORS[1] : HEX_COLORS[hex.type] || '#8bc34a';
        drawHexagon(x, y, color);

        ctx.font = `${10 * scale}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#000';
        ctx.fillStyle = '#fff';
        ctx.strokeText(hex.cost, x, y);
        ctx.fillText(hex.cost, x, y);
    });

    // Рисуем муравейник картинкой
    arenaData.home.forEach(home => {
        const {x, y} = hexToPixel(home.q, home.r);
        if (images.house) {
            const size = HEX_RADIUS * 2.2 * scale;
            ctx.drawImage(images.house, x - size/2, y - size/2, size, size);
        }
    });

    // Рисуем ресурсы (еду) картинками
    arenaData.food.forEach(food => {
        const {x, y} = hexToPixel(food.q, food.r);
        let img = null;
        if (food.type === 1) img = images.apple;
        if (food.type === 2) img = images.bread;
        if (food.type === 3) img = images.nectar;
        if (img) {
            const size = HEX_RADIUS * 1.5 * scale;
            ctx.drawImage(img, x - size/2, y - size/2, size, size);
            // Количество поверх картинки
            ctx.font = `${10 * scale}px Arial`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.lineWidth = 2;
            ctx.strokeStyle = '#000';
            ctx.fillStyle = '#fff';
            ctx.strokeText(food.amount, x, y);
            ctx.fillText(food.amount, x, y);
        } else {
            const color = FOOD_COLORS[food.type] || '#4caf50';
            drawObject(x, y, color, HEX_RADIUS * 0.6, food.amount);
        }
    });
    
    // Рисуем врагов
    arenaData.enemies.forEach(enemy => {
        const {x, y} = hexToPixel(enemy.q, enemy.r);
        drawAntImage(x, y, enemy.type, true);
    });
    
    // Рисуем наших муравьев
    arenaData.ants.forEach(ant => {
        const {x, y} = hexToPixel(ant.q, ant.r);
        drawAntImage(x, y, ant.type);
        
        // Показываем направление движения
        if (ant.move && ant.move.length > 0) {
            const target = ant.move[ant.move.length - 1];
            const targetPos = hexToPixel(target.q, target.r);
            
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(targetPos.x, targetPos.y);
            ctx.strokeStyle = ANT_COLORS[ant.type] || '#ffe600';
            ctx.lineWidth = 2 * scale;
            ctx.stroke();
            
            // Стрелка
            const angle = Math.atan2(targetPos.y - y, targetPos.x - x);
            const arrowSize = 5 * scale;
            ctx.beginPath();
            ctx.moveTo(targetPos.x, targetPos.y);
            ctx.lineTo(
                targetPos.x - arrowSize * Math.cos(angle - Math.PI/6),
                targetPos.y - arrowSize * Math.sin(angle - Math.PI/6)
            );
            ctx.lineTo(
                targetPos.x - arrowSize * Math.cos(angle + Math.PI/6),
                targetPos.y - arrowSize * Math.sin(angle + Math.PI/6)
            );
            ctx.closePath();
            ctx.fillStyle = ANT_COLORS[ant.type] || '#ffe600';
            ctx.fill();
        }
    });
    
    // Обновляем информационные панели
    updateInfoPanels();
}

// Обновление информационных панелей
function updateInfoPanels() {
    // Наши муравьи
    antsListElement.innerHTML = '';
    arenaData.ants.forEach(ant => {
        const antElement = document.createElement('div');
        antElement.className = 'entity-item';
        antElement.innerHTML = `
            <div>
                <strong>${ANT_TYPES[ant.type] || 'Муравей'} ${ant.id.slice(0, 8)}</strong>
                <div>Тип: ${ant.type} | Координаты: (${ant.q}, ${ant.r})</div>
                <div>Здоровье: ${ant.health}</div>
                <div class="health-bar">
                    <div class="health-fill" style="width: ${ant.health}%; background: ${ant.health > 50 ? '#2ecc71' : ant.health > 25 ? '#f39c12' : '#e74c3c'}"></div>
                </div>
            </div>
        `;
        antsListElement.appendChild(antElement);
    });
    
    // Враги
    enemiesListElement.innerHTML = '';
    arenaData.enemies.forEach(enemy => {
        const enemyElement = document.createElement('div');
        enemyElement.className = 'entity-item';
        enemyElement.innerHTML = `
            <div>
                <strong>Враг типа ${enemy.type}</strong>
                <div>Координаты: (${enemy.q}, ${enemy.r})</div>
                <div>Здоровье: ${enemy.health} | Атака: ${enemy.attack}</div>
            </div>
        `;
        enemiesListElement.appendChild(enemyElement);
    });
    
    // Ресурсы
    foodListElement.innerHTML = '';
    arenaData.food.forEach(food => {
        const foodElement = document.createElement('div');
        foodElement.className = 'entity-item';
        foodElement.innerHTML = `
            <div>
                <strong>${FOOD_TYPES[food.type] || 'Ресурс'}</strong>
                <div>Координаты: (${food.q}, ${food.r})</div>
                <div>Количество: ${food.amount}</div>
            </div>
        `;
        foodListElement.appendChild(foodElement);
    });
}

// Функция для загрузки данных с сервера
async function fetchArenaData() {
    try {
        loadingElement.style.display = 'flex';
        statusTextElement.textContent = 'Загрузка данных...';
        
        const response = await fetch('https://games-test.datsteam.dev/api/arena', {
            headers: {
                'X-Auth-Token': 'b12a46bf-db96-4d30-9add-72d1184e05d3'
            }
        });
        

        
        arenaData = {
    "ants": [
        {
            "q": 37,
            "r": 88,
            "type": 1,
            "health": 180,
            "id": "e37da490-6a26-49dd-81ce-ecc6cbe891a6",
            "food": {
                "type": 0,
                "amount": 0
            }
        },
        {
            "q": 37,
            "r": 88,
            "type": 0,
            "health": 130,
            "id": "9b58b3d8-4e73-4eda-9112-090c53335826",
            "food": {
                "type": 0,
                "amount": 0
            }
        },
        {
            "q": 37,
            "r": 88,
            "type": 2,
            "health": 80,
            "id": "c119d30f-ca0d-436a-b2ce-1d4d616d606a",
            "food": {
                "type": 0,
                "amount": 0
            }
        }
    ],
    "enemies": [],
    "map": [
        {
            "q": 35,
            "r": 84,
            "cost": 1,
            "type": 2
        },
        {
            "q": 39,
            "r": 89,
            "cost": 1,
            "type": 2
        },
        {
            "q": 37,
            "r": 89,
            "cost": 1,
            "type": 2
        },
        {
            "q": 34,
            "r": 89,
            "cost": 1,
            "type": 2
        },
        {
            "q": 39,
            "r": 86,
            "cost": 1,
            "type": 2
        },
        {
            "q": 37,
            "r": 92,
            "cost": 1,
            "type": 2
        },
        {
            "q": 36,
            "r": 88,
            "cost": 1,
            "type": 2
        },
        {
            "q": 37,
            "r": 84,
            "cost": 1,
            "type": 2
        },
        {
            "q": 38,
            "r": 85,
            "cost": 1,
            "type": 2
        },
        {
            "q": 33,
            "r": 89,
            "cost": 30,
            "type": 5
        },
        {
            "q": 36,
            "r": 92,
            "cost": 2,
            "type": 3
        },
        {
            "q": 38,
            "r": 84,
            "cost": 1,
            "type": 2
        },
        {
            "q": 40,
            "r": 87,
            "cost": 1,
            "type": 4
        },
        {
            "q": 37,
            "r": 86,
            "cost": 1,
            "type": 2
        },
        {
            "q": 38,
            "r": 90,
            "cost": 1,
            "type": 2
        },
        {
            "q": 36,
            "r": 84,
            "cost": 1,
            "type": 2
        },
        {
            "q": 34,
            "r": 85,
            "cost": 1,
            "type": 2
        },
        {
            "q": 35,
            "r": 89,
            "cost": 1,
            "type": 2
        },
        {
            "q": 39,
            "r": 91,
            "cost": 1,
            "type": 2
        },
        {
            "q": 38,
            "r": 89,
            "cost": 1,
            "type": 2
        },
        {
            "q": 40,
            "r": 88,
            "cost": 1,
            "type": 2
        },
        {
            "q": 39,
            "r": 84,
            "cost": 1,
            "type": 2
        },
        {
            "q": 37,
            "r": 85,
            "cost": 1,
            "type": 2
        },
        {
            "q": 38,
            "r": 87,
            "cost": 1,
            "type": 2
        },
        {
            "q": 34,
            "r": 86,
            "cost": 1,
            "type": 2
        },
        {
            "q": 35,
            "r": 85,
            "cost": 1,
            "type": 2
        },
        {
            "q": 33,
            "r": 87,
            "cost": 1,
            "type": 4
        },
        {
            "q": 40,
            "r": 90,
            "cost": 2,
            "type": 3
        },
        {
            "q": 36,
            "r": 87,
            "cost": 1,
            "type": 1
        },
        {
            "q": 38,
            "r": 91,
            "cost": 1,
            "type": 2
        },
        {
            "q": 33,
            "r": 88,
            "cost": 1,
            "type": 4
        },
        {
            "q": 39,
            "r": 87,
            "cost": 1,
            "type": 2
        },
        {
            "q": 37,
            "r": 88,
            "cost": 1,
            "type": 1
        },
        {
            "q": 34,
            "r": 87,
            "cost": 1,
            "type": 2
        },
        {
            "q": 34,
            "r": 91,
            "cost": 1,
            "type": 4
        },
        {
            "q": 35,
            "r": 91,
            "cost": 1,
            "type": 2
        },
        {
            "q": 36,
            "r": 90,
            "cost": 1,
            "type": 2
        },
        {
            "q": 38,
            "r": 86,
            "cost": 1,
            "type": 2
        },
        {
            "q": 39,
            "r": 92,
            "cost": 1,
            "type": 2
        },
        {
            "q": 41,
            "r": 88,
            "cost": 1,
            "type": 4
        },
        {
            "q": 37,
            "r": 87,
            "cost": 1,
            "type": 1
        },
        {
            "q": 40,
            "r": 89,
            "cost": 1,
            "type": 2
        },
        {
            "q": 37,
            "r": 90,
            "cost": 1,
            "type": 2
        },
        {
            "q": 36,
            "r": 91,
            "cost": 1,
            "type": 2
        },
        {
            "q": 40,
            "r": 86,
            "cost": 2,
            "type": 3
        },
        {
            "q": 39,
            "r": 90,
            "cost": 1,
            "type": 2
        },
        {
            "q": 36,
            "r": 85,
            "cost": 1,
            "type": 2
        },
        {
            "q": 35,
            "r": 88,
            "cost": 1,
            "type": 2
        },
        {
            "q": 35,
            "r": 90,
            "cost": 1,
            "type": 2
        },
        {
            "q": 39,
            "r": 88,
            "cost": 1,
            "type": 2
        },
        {
            "q": 34,
            "r": 90,
            "cost": 1,
            "type": 2
        },
        {
            "q": 34,
            "r": 88,
            "cost": 1,
            "type": 2
        },
        {
            "q": 38,
            "r": 88,
            "cost": 1,
            "type": 2
        },
        {
            "q": 36,
            "r": 89,
            "cost": 1,
            "type": 2
        },
        {
            "q": 38,
            "r": 92,
            "cost": 1,
            "type": 2
        },
        {
            "q": 35,
            "r": 87,
            "cost": 1,
            "type": 2
        },
        {
            "q": 35,
            "r": 86,
            "cost": 1,
            "type": 2
        },
        {
            "q": 35,
            "r": 92,
            "cost": 2,
            "type": 3
        },
        {
            "q": 39,
            "r": 85,
            "cost": 2,
            "type": 3
        },
        {
            "q": 36,
            "r": 86,
            "cost": 1,
            "type": 2
        },
        {
            "q": 37,
            "r": 91,
            "cost": 1,
            "type": 2
        }
    ],
    "food": [
        {
            "q": 40,
            "r": 90,
            "type": 1,
            "amount": 6
        },
        {
            "q": 34,
            "r": 91,
            "type": 1,
            "amount": 8
        },
        {
            "q": 41,
            "r": 88,
            "type": 1,
            "amount": 2
        },
        {
            "q": 38,
            "r": 92,
            "type": 2,
            "amount": 10
        },
        {
            "q": 35,
            "r": 87,
            "type": 2,
            "amount": 12
        }
    ],
    "turnNo": 66,
    "nextTurnIn": 1.158,
    "home": [
        {
            "q": 37,
            "r": 87
        },
        {
            "q": 36,
            "r": 87
        },
        {
            "q": 37,
            "r": 88
        }
    ],
    "score": 0,
    "spot": {
        "q": 37,
        "r": 88
    }
}
        
        // Обновляем статистику
        scoreElement.textContent = arenaData.score;
        
        // Рассчитываем границы для центрирования карты
        calculateMapBounds();
        
        // Центрируем карту на муравейнике
        centerOnHome();
        
        // Рисуем арену
        drawArena();
        
        statusTextElement.textContent = 'Данные успешно загружены';
        setTimeout(() => {
            loadingElement.style.display = 'none';
        }, 500);
    } catch (error) {
        console.error('Ошибка при загрузке данных:', error);
        statusTextElement.textContent = `Ошибка: ${error.message}`;
        loadingElement.style.display = 'none';
    }
}

// Рассчитываем границы карты для центрирования
function calculateMapBounds() {
    if (!arenaData || !arenaData.map.length) return;
    
    let minQ = Infinity, maxQ = -Infinity;
    let minR = Infinity, maxR = -Infinity;
    
    // Собираем все координаты из всех объектов
    const allCoords = [
        ...arenaData.map.map(h => ({q: h.q, r: h.r})),
        ...arenaData.ants.map(a => ({q: a.q, r: a.r})),
        ...arenaData.enemies.map(e => ({q: e.q, r: e.r})),
        ...arenaData.food.map(f => ({q: f.q, r: f.r})),
        ...arenaData.home.map(h => ({q: h.q, r: h.r}))
    ];
    
    // Находим границы
    allCoords.forEach(coord => {
        minQ = Math.min(minQ, coord.q);
        maxQ = Math.max(maxQ, coord.q);
        minR = Math.min(minR, coord.r);
        maxR = Math.max(maxR, coord.r);
    });
    
    // Рассчитываем размеры в пикселях
    const widthInHexes = maxQ - minQ + 1;
    const heightInHexes = maxR - minR + 1;
    
    const pixelWidth = widthInHexes * HEX_WIDTH * 0.75 + HEX_RADIUS;
    const pixelHeight = heightInHexes * HEX_HEIGHT + HEX_HEIGHT * 0.5;
    
    // Устанавливаем размеры canvas
    canvasWidth = Math.max(800, pixelWidth);
    canvasHeight = Math.max(600, pixelHeight);
    canvas.width = canvasWidth;
    canvas.height = canvasHeight;
    
    // Начальный масштаб
    scale = 1;
}

// Центрирование на муравейнике
function centerOnHome() {
    if (!arenaData || !arenaData.home || arenaData.home.length === 0) return;
    
    // Берем первый гекс муравейника как центральный
    const homeHex = arenaData.home[0];
    const {x, y} = hexToPixel(homeHex.q, homeHex.r);
    
    // Центрируем муравейник
    offsetX = canvasWidth / 2 - x;
    offsetY = canvasHeight / 2 - y;
}

// Обработчики событий для масштабирования и перемещения
canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    
    const zoomIntensity = 0.1;
    const mouseX = e.clientX - canvas.getBoundingClientRect().left;
    const mouseY = e.clientY - canvas.getBoundingClientRect().top;
    
    const wheel = e.deltaY < 0 ? 1 : -1;
    const zoom = Math.exp(wheel * zoomIntensity);
    
    // Сохраняем старый масштаб
    const oldScale = scale;
    
    // Применяем масштаб
    scale *= zoom;
    
    // Ограничиваем масштаб
    scale = Math.max(0.5, Math.min(scale, 3));
    
    // Если масштаб не изменился (из-за ограничений), не меняем смещение
    if (scale === oldScale) return;
    
    // Вычисляем смещение для сохранения позиции курсора
    offsetX -= (mouseX - offsetX) * (scale / oldScale - 1);
    offsetY -= (mouseY - offsetY) * (scale / oldScale - 1);
    
    drawArena();
});

canvas.addEventListener('mousedown', (e) => {
    isDragging = true;
    lastX = e.clientX;
    lastY = e.clientY;
    canvas.style.cursor = 'grabbing';
});

canvas.addEventListener('mousemove', (e) => {
    const mouseX = e.clientX - canvas.getBoundingClientRect().left;
    const mouseY = e.clientY - canvas.getBoundingClientRect().top;
    
    // Обновляем отображение координат
    coordinatesElement.textContent = `Координаты: (${Math.round(mouseX)}, ${Math.round(mouseY)})`;
    
    if (isDragging) {
        const dx = e.clientX - lastX;
        const dy = e.clientY - lastY;
        
        offsetX += dx;
        offsetY += dy;
        
        lastX = e.clientX;
        lastY = e.clientY;
        
        drawArena();
    }
});

canvas.addEventListener('mouseup', () => {
    isDragging = false;
    canvas.style.cursor = 'grab';
});

canvas.addEventListener('mouseleave', () => {
    isDragging = false;
    canvas.style.cursor = 'default';
});

// Инициализация
Promise.all([
    loadImages().catch(e => console.error(e)),
    fetchArenaData(),
    refreshBtn.addEventListener('click', () => {
        location.reload();
    })
]);