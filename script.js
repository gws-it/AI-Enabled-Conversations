const input = document.getElementById("chat-input");
const log = document.getElementById("chat-log");

input.addEventListener("keypress", async function (e) {
    if (e.key === "Enter" && input.value.trim() !== "") {
        const question = input.value.trim();
        appendMessage("You", question);
        input.value = "";

        // Create a placeholder message for the streaming response
        const responseDiv = document.createElement("div");
        responseDiv.innerHTML = `<strong>Black Soldier Fly:</strong> <span class="response-content"></span>`;
        log.appendChild(responseDiv);
        log.scrollTop = log.scrollHeight;
        
        const responseContent = responseDiv.querySelector('.response-content');

        try {
            const res = await fetch("https://api.openai.com/v1/chat/completions", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": 'Bearer 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'
                },
                body: JSON.stringify({
                    model: "gpt-4",
                    messages: [
                        {
                            role: "system",
                            content: "You are a black soldier fly in a compost bin in Singapore. " +
                            " Answer the question as if you were the fly," +
                            " and keep it informative but simple and a little fun. For questions that" +
                            " don't need a long answer, keep it concise."
                        },
                        {
                            role: "user",
                            content: question
                        }
                    ],
                    stream: true  // Enable streaming
                })
            });

            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let fullResponse = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        
                        if (data === '[DONE]') {
                            continue;
                        }

                        try {
                            const parsed = JSON.parse(data);
                            const content = parsed.choices?.[0]?.delta?.content;
                            
                            if (content) {
                                fullResponse += content;
                                responseContent.textContent = fullResponse;
                                log.scrollTop = log.scrollHeight;
                            }
                        } catch (parseError) {
                            // Skip malformed JSON chunks
                            continue;
                        }
                    }
                }
            }

        } catch (error) {
            responseContent.textContent = "Oops! I couldn't respond just now. Please try again.";
            console.error("Error details:", error);
        }
    }
});

function appendMessage(sender, text) {
    const msg = document.createElement("div");
    msg.innerHTML = `<strong>${sender}:</strong> ${text}`;
    
    // Add a class based on the sender
    if (sender === "You") {
        msg.classList.add("user-message");
    } else {
        msg.classList.add("ai-message");
    }
    
    log.appendChild(msg);
    log.scrollTop = log.scrollHeight;
}

// Show a welcome message on load
window.addEventListener("DOMContentLoaded", () => {
    appendMessage("Black Soldier Fly", "Hi there! I'm a black soldier fly living in a compost bin in Singapore. " +
        " Ask me anything about sustainability, composting, or my daily life!");
});