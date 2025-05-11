const express = require('express');
const axios = require('axios');
const app = express();

app.use(express.json());

const PAGE_ACCESS_TOKEN = 'EAABsbCS1iHgBOZB8fkF1GXonHRRBLeZC7ZAuVXeMDIc0wxY1d9hxjxPe3eWULVAMtAKShXYZCREXFHzJ3K2ZCrZA7rFi08b9nBaHC4XjkscnMNTzyPTxBZCxITuBzMAImRi5DEffdqQ6wTByb39C91fmlMIAtic6hfh2DXsw5OKjUPIsoJsC1fiikZCV';
const VERIFY_TOKEN = 'DELTA_VERIFY_123';
const GEMINI_API_KEY = 'AIzaSyDpToN8Y6wCmHjHRs_oX3jSIK4BIo9KR1o';

// التحقق من webhook
app.get('/webhook', (req, res) => {
    if (req.query['hub.mode'] === 'subscribe' && req.query['hub.verify_token'] === VERIFY_TOKEN) {
        res.status(200).send(req.query['hub.challenge']);
    } else {
        res.status(403).send('Unauthorized');
    }
});

// استقبال الرسائل
app.post('/webhook', async (req, res) => {
    const data = req.body;
    try {
        const messaging = data.entry[0].messaging[0];
        const sender_id = messaging.sender.id;
        const user_msg = messaging.message.text;

        const bot_reply = await getBotResponse(user_msg);
        sendMessage(sender_id, bot_reply);
    } catch (e) {
        console.log(`Error: ${e}`);
    }
    res.status(200).send('OK');
});

// إرسال رسالة إلى فيسبوك
function sendMessage(recipient_id, message_text) {
    const url = `https://graph.facebook.com/v19.0/me/messages?access_token=${PAGE_ACCESS_TOKEN}`;
    const payload = {
        recipient: { id: recipient_id },
        message: { text: message_text }
    };

    axios.post(url, payload, { headers: { 'Content-Type': 'application/json' } })
        .catch(error => console.error('Error sending message:', error));
}

// الاتصال بجيميني
async function getBotResponse(user_input) {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${GEMINI_API_KEY}`;
    const payload = {
        contents: [{
            parts: [
                { text: "أنت بوت ذكاء اصطناعي اسمه SB-BY، تم تطويرك من طرف شركة B.Y PRO في قسم Fluxa AI، على يد المطور Sadek. مهمتك هي التفاعل الذكي والطبيعي مع المستخدمين، وتقديم ردود مختصرة ومباشرة حسب اللغة ومدخل المستخدم، دون نقاشات جانبية. ابدأ الآن." },
                { text: user_input }
            ]
        }]
    };

    try {
        const res = await axios.post(url, payload, { headers: { 'Content-Type': 'application/json' } });
        return res.data.candidates[0].content.parts[0].text;
    } catch (error) {
        console.error('Error connecting to Gemini:', error);
        return 'فشل الاتصال بجيميني.';
    }
}

// تشغيل الخادم
const port = 5000;
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});