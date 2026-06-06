
let lastFrames = {};
let isFullscreen = false;
let selectedDevice = null;

async function fetchFrames() {
    try {
        const response = await fetch("{% url 'picam_data' %}", { cache: "no-store" });
        if (!response.ok) throw new Error("Network response was not ok");
        const data = await response.json();
        return data.frames;
    } catch (error) {
        console.error("Error fetching frames:", error);
        return {};
    }
}

async function renderCameras() {
    const frames = await fetchFrames();
    const grid = document.getElementById('grid');

    for (const [deviceId, image] of Object.entries(frames)) {

        if (selectedDevice == deviceId) {

            let camBox = document.getElementById(`fullscreen-${deviceId}`);
            let imgElement = document.getElementById(`fullscreen-img-${deviceId}`);

            // 기존에 없으면 새로 생성
            if (!camBox) {
                camBox = document.createElement("div");
                camBox.className = "fullscreen-box";
                camBox.id = `fullscreen-${deviceId}`;
                camBox.innerHTML = `
                    <h3>${deviceId}</h3>
                    <img id="fullscreen-img-${deviceId}" src="" loading="lazy" style="transition: opacity 0.1s;">
                `;
                camBox.addEventListener("mousedown", () => toggleFullscreen(deviceId));
                grid.appendChild(camBox);
                imgElement = document.getElementById(`img-${deviceId}`);
            }

            // 🔄 기존 이미지와 다를 때만 업데이트 → 깜박임 방지
            if (lastFrames[deviceId] !== image) {
                lastFrames[deviceId] = image;
                let newImg = new Image();
                newImg.src = `data:image/jpeg;base64,${image}`;

                newImg.onload = () => {
                    imgElement.src = newImg.src;
                };
            }

        } else if (!isFullscreen) {

            let camBox = document.getElementById(`cam-${deviceId}`);
            let imgElement = document.getElementById(`img-${deviceId}`);

            // 기존에 없으면 새로 생성
            if (!camBox) {
                camBox = document.createElement("div");
                camBox.className = "camera-box";
                camBox.id = `cam-${deviceId}`;
                camBox.innerHTML = `
                    <h3>${deviceId}</h3>
                    <img id="img-${deviceId}" src="" loading="lazy" style="transition: opacity 0.1s;">
                `;
                camBox.addEventListener("mousedown", () => toggleFullscreen(deviceId));
                grid.appendChild(camBox);
                imgElement = document.getElementById(`img-${deviceId}`);
            }

            // 🔄 기존 이미지와 다를 때만 업데이트 → 깜박임 방지
            if (lastFrames[deviceId] !== image) {
                lastFrames[deviceId] = image;
                let newImg = new Image();
                newImg.src = `data:image/jpeg;base64,${image}`;

                newImg.onload = () => {
                    imgElement.src = newImg.src;
                };
            }
        }             
    }
}

// ✅ Fullscreen 모드 토글
function toggleFullscreen(deviceId) {
    const grid = document.getElementById('grid');

    if (!isFullscreen) {
        // 📌 Fullscreen 모드 활성화
        isFullscreen = true;
        selectedDevice = deviceId;
        
    } else {
        // 📌 Fullscreen 모드 종료 (원래 Grid 복귀)
        exitFullscreen();
    }
}

// ✅ Fullscreen 모드 해제 (원래 Grid 복귀)
function exitFullscreen() {
    isFullscreen = false;
    selectedDevice = null;
    document.getElementById('grid').innerHTML = "";
    renderCameras();
}

// 🔄 100ms마다 실행
setInterval(renderCameras, 100);
renderCameras();