# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from dashscope import MultiModalConversation, Generation
import dashscope
import os
import re

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

app = Flask(__name__)
CORS(app)

def is_multiple_choice(question: str) -> bool:
    patterns = [r'\b[A-D]\.\s', r'\([A-D]\)', r'选项[：:]?\s*[A-D]', r'四个选项']
    return any(re.search(p, question, re.IGNORECASE) for p in patterns)

@app.route('/grade', methods=['POST'])
def grade_mistake():
    data = request.json
    question = data.get('question', '').strip()
    user_answer = data.get('user_answer', '').strip()
    image_base64 = data.get('image', '')

    if not question or not user_answer:
        return jsonify({"error": "题目和答案不能为空"}), 400

    is_mc = is_multiple_choice(question)
    system_prompt = (
         "你是一名严谨的中学教师，请根据题目类型采用以下规则批改：\n\n"
        
        "📌 如果题目是【选择题】（明显包含 A、B、C、D 等选项）：\n"
        "- 【正确答案】仅写出标准选项字母（如：C）；\n"
        "- 【解析】先直接说明“正确选项是 X，因为……”，然后逐条分析其他每个选项为何错误。\n\n"
        
        "📌 如果题目是【非选择题】（如填空题、计算题、解答题等）：\n"
        "- 【正确答案】写出完整的标准答案；\n"
        "- 【解析】给出完整、规范的正确解题过程，步骤清晰,简单明了。\n\n"
        
        "此外，所有题目都必须包含：\n"
        "- 【考点】指出考查的具体知识点；\n"
        "- 【错因】结合学生答案，判断是“粗心”还是“概念不清”。\n\n"
        
        "请严格按以下五点格式作答，每点独立成段：\n"
        "1. 【判断】\n"
        "2. 【正确答案】\n"
        "3. 【解析】\n"
        "4. 【考点】\n"
        "5. 【错因】\n\n"
    )
    user_prompt = f"题目：{question}\n我的答案：{user_answer}"

    try:
        if image_base64:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': [{'image': image_base64}, {'text': user_prompt}]}
            ]
            response = MultiModalConversation.call(model='qwen-vl-plus', messages=messages)
        else:
            response = Generation.call(
                model='qwen-plus',
                messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
            )

        if response.status_code == 200:
            ai_text = response.output.choices[0].message.content
            return jsonify({"ai_feedback": ai_text})
        else:
            return jsonify({"error": f"AI 错误: {response.code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def hello():
    return "✅ Mistake Book Backend is running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))