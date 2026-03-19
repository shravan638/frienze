const express = require("express");
const fetch = require("node-fetch");
const path = require("path");

const app = express();
app.use(express.json());
app.use(express.static(__dirname));

app.post("/api/chat", async (req, res) => {
    try {
        const { messages } = req.body;

        const response = await fetch("https://api.openai.com/v1/chat/completions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`
            },
            body: JSON.stringify({
                model: "gpt-3.5-turbo",
                max_tokens: 1024,
                messages: [
                    {
                        role: "system",
                        content: "You are Frienze, a smart and helpful AI assistant. Answer the user's questions directly and accurately. If they ask something factual, answer it. If they want to code, help them code. If they want to chat, chat with them. Be natural, friendly, and concise."
                    },
                    ...messages
                ]
            })
        });

        const data = await response.json();
        if (data.error) return res.status(500).json({ error: data.error.message });

        const reply = data.choices[0].message.content;
        res.status(200).json({ reply });

    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get("*", (req, res) => {
    res.sendFile(path.join(__dirname, "frienze-ai.html"));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Frienze running on port ${PORT}`));
