/* =====================================
   ELEMENTOS
===================================== */

const loginScreen = document.getElementById("loginScreen");
const app = document.getElementById("app");

const loginForm = document.getElementById("loginForm");

const togglePassword =
    document.getElementById("togglePassword");

const passwordInput =
    document.getElementById("password");

const uploadModal =
    document.getElementById("uploadModal");

const addSourceBtn =
    document.getElementById("addSourceBtn");

const addSourceBtn2 =
    document.getElementById("addSourceBtn2");

const emptyUploadBtn =
    document.getElementById("emptyUploadBtn");

const closeModal =
    document.getElementById("closeModal");

const cancelUpload =
    document.getElementById("cancelUpload");

const fileInput =
    document.getElementById("fileInput");

const dropZone =
    document.getElementById("dropZone");

const selectedFiles =
    document.getElementById("selectedFiles");

const sourcesList =
    document.getElementById("sourcesList");

const sourceCount =
    document.getElementById("sourceCount");

const chatInput =
    document.getElementById("chatInput");

const sendMessage =
    document.getElementById("sendMessage");

const chatMessages =
    document.getElementById("chatMessages");

const questionCount =
    document.getElementById("questionCount");

const openSidebar =
    document.getElementById("openSidebar");

const closeSidebar =
    document.getElementById("closeSidebar");

const sidebar =
    document.getElementById("sidebar");

const newProjectBtn =
    document.getElementById("newProjectBtn");


/* =====================================
   LOGIN
===================================== */

loginForm.addEventListener("submit", function(event) {

    event.preventDefault();

    const email =
        document.getElementById("email").value;

    const password =
        document.getElementById("password").value;

    if (!email || !password) {
        alert("Preencha todos os campos.");
        return;
    }

    /*
        FUTURO BACKEND:

        Aqui futuramente vocês poderão fazer:

        fetch("/api/login", {
            method: "POST",
            body: JSON.stringify({
                email,
                password
            })
        })

        Por enquanto vamos apenas entrar
        na aplicação.
    */

    loginScreen.classList.add("hidden");

    app.classList.remove("hidden");

});


/* =====================================
   MOSTRAR / ESCONDER SENHA
===================================== */

togglePassword.addEventListener("click", function() {

    if (passwordInput.type === "password") {

        passwordInput.type = "text";

        togglePassword.innerHTML =
            '<i class="fa-regular fa-eye-slash"></i>';

    } else {

        passwordInput.type = "password";

        togglePassword.innerHTML =
            '<i class="fa-regular fa-eye"></i>';

    }

});


/* =====================================
   MODAL
===================================== */

function openUploadModal() {

    uploadModal.classList.remove("hidden");

}

function closeUploadModal() {

    uploadModal.classList.add("hidden");

    selectedFiles.innerHTML = "";

    fileInput.value = "";

}


addSourceBtn.addEventListener(
    "click",
    openUploadModal
);

addSourceBtn2.addEventListener(
    "click",
    openUploadModal
);

emptyUploadBtn.addEventListener(
    "click",
    openUploadModal
);

closeModal.addEventListener(
    "click",
    closeUploadModal
);

cancelUpload.addEventListener(
    "click",
    closeUploadModal
);


/* FECHAR CLICANDO FORA */

uploadModal.addEventListener(
    "click",
    function(event) {

        if (event.target === uploadModal) {
            closeUploadModal();
        }

    }
);


/* =====================================
   SELEÇÃO DE ARQUIVOS
===================================== */

fileInput.addEventListener(
    "change",
    function() {

        showSelectedFiles(
            Array.from(fileInput.files)
        );

    }
);


function showSelectedFiles(files) {

    selectedFiles.innerHTML = "";

    files.forEach(file => {

        const div =
            document.createElement("div");

        div.className =
            "selected-file";

        div.innerHTML = `
            <i class="fa-solid fa-file"></i>

            <span>${file.name}</span>
        `;

        selectedFiles.appendChild(div);

    });

}


/* =====================================
   DRAG AND DROP
===================================== */

dropZone.addEventListener(
    "dragover",
    function(event) {

        event.preventDefault();

        dropZone.classList.add("dragover");

    }
);


dropZone.addEventListener(
    "dragleave",
    function() {

        dropZone.classList.remove("dragover");

    }
);


dropZone.addEventListener(
    "drop",
    function(event) {

        event.preventDefault();

        dropZone.classList.remove("dragover");

        const files =
            Array.from(event.dataTransfer.files);

        showSelectedFiles(files);

    }
);


/* =====================================
   ADICIONAR ARQUIVO
===================================== */

document
    .getElementById("confirmUpload")
    .addEventListener(
        "click",
        function() {

            const files =
                Array.from(fileInput.files);

            if (files.length === 0) {

                alert(
                    "Selecione pelo menos um arquivo."
                );

                return;

            }


            files.forEach(file => {

                addSourceToInterface(file);

            });


            closeUploadModal();

        }
    );


function addSourceToInterface(file) {

    const extension =
        file.name
            .split(".")
            .pop()
            .toLowerCase();


    let icon =
        "fa-file";

    let typeClass =
        "";


    if (extension === "pdf") {

        icon = "fa-file-pdf";
        typeClass = "pdf";

    }

    else if (
        extension === "xlsx" ||
        extension === "xls" ||
        extension === "csv"
    ) {

        icon = "fa-file-excel";
        typeClass = "excel";

    }

    else if (
        extension === "doc" ||
        extension === "docx"
    ) {

        icon = "fa-file-word";
        typeClass = "doc";

    }


    const source =
        document.createElement("div");

    source.className =
        "source-card";


    source.innerHTML = `

        <div class="source-icon ${typeClass}">

            <i class="fa-solid ${icon}"></i>

        </div>


        <div class="source-info">

            <strong>
                ${file.name}
            </strong>

            <span>
                ${extension.toUpperCase()} •
                ${formatFileSize(file.size)}
            </span>

        </div>


        <button class="source-menu">

            <i class="fa-solid fa-ellipsis"></i>

        </button>

    `;


    /*
        Inserimos antes da área
        "Adicionar nova fonte"
    */

    const empty =
        document.getElementById("emptySource");

    sourcesList.insertBefore(
        source,
        empty
    );


    updateSourceCount();

}


/* =====================================
   TAMANHO DO ARQUIVO
===================================== */

function formatFileSize(bytes) {

    if (bytes === 0)
        return "0 Bytes";


    const sizes = [
        "Bytes",
        "KB",
        "MB",
        "GB"
    ];


    const i =
        Math.floor(
            Math.log(bytes) /
            Math.log(1024)
        );


    return (
        Math.round(
            bytes /
            Math.pow(1024, i) *
            100
        ) / 100
    ) + " " + sizes[i];

}


/* =====================================
   CONTADOR DE FONTES
===================================== */

function updateSourceCount() {

    const cards =
        sourcesList.querySelectorAll(
            ".source-card"
        );

    sourceCount.textContent =
        cards.length;

}


/* =====================================
   CHAT
===================================== */

sendMessage.addEventListener(
    "click",
    sendUserMessage
);


chatInput.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendUserMessage();

        }

    }
);


function sendUserMessage() {

    const message =
        chatInput.value.trim();


    if (!message)
        return;


    addUserMessage(message);


    chatInput.value = "";


    incrementQuestionCount();


    /*
        SIMULAÇÃO DA IA

        Futuramente aqui entra
        a chamada para o backend.

        Exemplo:

        fetch("/api/chat", {
            method: "POST",
            body: JSON.stringify({
                question: message,
                projectId: 1
            })
        })
    */


    showTyping();


    setTimeout(
        function() {

            removeTyping();

            generateAIResponse(message);

        },
        1200
    );

}


/* =====================================
   MENSAGEM DO USUÁRIO
===================================== */

function addUserMessage(message) {

    const div =
        document.createElement("div");

    div.className =
        "message user-message";


    div.innerHTML = `

        <div class="message-avatar">
            MD
        </div>

        <div class="message-content">

            <div class="message-author">
                Você
            </div>

            <p>
                ${escapeHTML(message)}
            </p>

            <span class="message-time">
                Agora
            </span>

        </div>

    `;


    chatMessages.appendChild(div);


    scrollChat();

}


/* =====================================
   RESPOSTA DA IA
===================================== */

function generateAIResponse(question) {

    let response = "";


    const lower =
        question.toLowerCase();


    if (
        lower.includes("resumo") ||
        lower.includes("resuma")
    ) {

        response = `
            Com base nas fontes adicionadas ao projeto,
            os documentos apresentam informações relacionadas
            aos principais conceitos de Inteligência Artificial,
            suas aplicações e fundamentos.
            <br><br>
            <strong>Observação:</strong>
            esta resposta está simulada no front-end.
            No sistema final, a IA utilizará o conteúdo real
            dos arquivos processados pelo backend.
        `;

    }

    else if (
        lower.includes("assunto") ||
        lower.includes("tema")
    ) {

        response = `
            O principal assunto identificado nas fontes está
            relacionado à área de Inteligência Artificial e
            aos conceitos utilizados para desenvolvimento
            de sistemas inteligentes.
            <br><br>
            No backend, essa análise será realizada utilizando
            os documentos enviados pelo usuário como contexto.
        `;

    }

    else if (
        lower.includes("conceito") ||
        lower.includes("importante")
    ) {

        response = `
            Alguns conceitos importantes identificados são:
            <br><br>

            • Inteligência Artificial<br>
            • Aprendizado de Máquina<br>
            • Processamento de dados<br>
            • Sistemas inteligentes<br>
            • Análise de informações
            <br><br>

            Esses resultados serão substituídos posteriormente
            pela análise real realizada pela IA.
        `;

    }

    else {

        response = `
            Entendi sua pergunta.
            <br><br>

            No momento, esta é uma resposta simulada
            para demonstrar o funcionamento da interface.
            Quando o backend estiver integrado,
            a IA poderá analisar o conteúdo dos documentos
            adicionados ao projeto e responder sua pergunta
            com base nessas informações.
        `;

    }


    addAIMessage(response);

}


/* =====================================
   MENSAGEM DA IA
===================================== */

function addAIMessage(message) {

    const div =
        document.createElement("div");

    div.className =
        "message ai-message";


    div.innerHTML = `

        <div class="message-avatar">

            <i class="fa-solid fa-sparkles"></i>

        </div>


        <div class="message-content">

            <div class="message-author">
                InsightIA
            </div>

            <p>
                ${message}
            </p>

            <span class="message-time">
                Agora
            </span>

        </div>

    `;


    chatMessages.appendChild(div);


    scrollChat();

}


/* =====================================
   LOADING DA IA
===================================== */

function showTyping() {

    const typing =
        document.createElement("div");

    typing.id =
        "typingMessage";

    typing.className =
        "message ai-message";


    typing.innerHTML = `

        <div class="message-avatar">

            <i class="fa-solid fa-sparkles"></i>

        </div>


        <div class="message-content">

            <div class="message-author">
                InsightIA
            </div>

            <p>
                Analisando suas fontes...
            </p>

        </div>

    `;


    chatMessages.appendChild(typing);

    scrollChat();

}


function removeTyping() {

    const typing =
        document.getElementById(
            "typingMessage"
        );


    if (typing)
        typing.remove();

}


/* =====================================
   CONTADOR DE PERGUNTAS
===================================== */

function incrementQuestionCount() {

    const current =
        parseInt(
            questionCount.textContent
        );


    questionCount.textContent =
        current + 1;

}


/* =====================================
   SCROLL CHAT
===================================== */

function scrollChat() {

    chatMessages.scrollTop =
        chatMessages.scrollHeight;

}


/* =====================================
   EVITAR HTML INJETADO
===================================== */

function escapeHTML(text) {

    const div =
        document.createElement("div");

    div.textContent =
        text;

    return div.innerHTML;

}


/* =====================================
   SIDEBAR MOBILE
===================================== */

openSidebar.addEventListener(
    "click",
    function() {

        sidebar.classList.add("open");

    }
);


closeSidebar.addEventListener(
    "click",
    function() {

        sidebar.classList.remove("open");

    }
);


/* =====================================
   NOVO PROJETO
===================================== */

newProjectBtn.addEventListener(
    "click",
    function() {

        const projectName =
            prompt(
                "Digite o nome do novo projeto:"
            );


        if (!projectName)
            return;


        const projectList =
            document.getElementById(
                "projectList"
            );


        const project =
            document.createElement("div");


        project.className =
            "project-item";


        project.innerHTML = `

            <span class="project-dot"></span>

            <span>
                ${escapeHTML(projectName)}
            </span>

        `;


        projectList.appendChild(project);

    }
);


/* =====================================
   SUGESTÕES DE PERGUNTAS
===================================== */

document
    .querySelectorAll(".suggestion-btn")
    .forEach(button => {

        button.addEventListener(
            "click",
            function() {

                chatInput.value =
                    this.textContent.trim();

                chatInput.focus();

            }
        );

    });


/* =====================================
   UPLOAD PELO CHAT
===================================== */

document
    .getElementById("chatAttach")
    .addEventListener(
        "click",
        openUploadModal
    );