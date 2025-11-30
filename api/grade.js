// api/grade.js
import { NextResponse } from 'next/server';
import { Qwen } from '@alicloud/dashscope-sdk';

const client = new Qwen({
  apiKey: process.env.DASHSCOPE_API_KEY,
});

function isMultipleChoice(question) {
  const patterns = [
    /\b[A-D]\.\s/i,
    /\([A-D]\)/i,
    /选项[：:]?\s*[A-D]/i,
    /四个选项/i
  ];
  return patterns.some(p => p.test(question));
}

export async function POST(request) {
  try {
    const data = await request.json();
    const { question, user_answer: userAnswer, image } = data;

    if (!question || !userAnswer) {
      return NextResponse.json({ error: "题目和答案不能为空" }, { status: 400 });
    }

    const isMc = isMultipleChoice(question);
    const systemPrompt = 
      ` "你是一名严谨的中学教师，请根据题目类型采用以下规则批改：\n\n"
        
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

    const userPrompt = `题目：${question}\n我的答案：${userAnswer}`;

    let response;
    if (image) {
      // 图像+文本（暂不支持，简化为文本）
      response = await client.chat.completions.create({
        model: 'qwen-plus',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ]
      });
    } else {
      response = await client.chat.completions.create({
        model: 'qwen-plus',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ]
      });
    }

    const aiFeedback = response.choices[0].message.content;
    return NextResponse.json({ ai_feedback: aiFeedback });

  } catch (error) {
    console.error('AI Error:', error);
    return NextResponse.json({ error: error.message || '批改失败' }, { status: 500 });
  }
}
