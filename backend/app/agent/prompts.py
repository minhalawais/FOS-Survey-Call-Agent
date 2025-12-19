"""
FOS Survey Agent - Urdu Prompts
All agent utterances in Urdu - replicates exact call agent behavior
"""

# =============================================================================
# CONVERSATION FLOW (Matches Telephony Agent)
# =============================================================================

# Initial greeting - identifies self and confirms worker identity
GREETING = """السلام علیکم! میں FOS سروے سینٹر سے بول رہا ہوں۔
کیا آپ {employee_name} صاحب سے بات ہو رہی ہے؟"""

# After worker confirms identity
IDENTITY_CONFIRMED = """شکریہ {employee_name} صاحب۔"""

# Survey introduction
SURVEY_INTRO = """آج میں آپ سے کچھ سوالات پوچھنا چاہتا ہوں۔ 
آپ کے جوابات مکمل طور پر رازدارانہ رہیں گے اور یہ ہماری کمپنی کو بہتر بنانے میں مدد کریں گے۔
آئیے شروع کرتے ہیں۔"""

# =============================================================================
# QUESTIONS (Matches Document Style)
# =============================================================================

# Ask a question
ASK_QUESTION = """سوال نمبر {question_number}: {question_text}"""

# Acknowledge response and move to next
ACKNOWLEDGE_NEXT = """شکریہ، اگلا سوال سنیں۔"""

# Short acknowledgment
ACKNOWLEDGE_SHORT = """جی، شکریہ۔"""

# =============================================================================
# CLARIFICATION & ERROR HANDLING
# =============================================================================

# Ask to repeat
REPEAT_REQUEST = """براہ کرم دوبارہ بتائیں، مجھے آپ کی بات واضح نہیں سمجھ آئی۔"""

# Speak louder
SPEAK_LOUDER = """آپ کی آواز واضح نہیں آ رہی۔ براہ کرم تھوڑا اونچا بولیں۔"""

# Continue prompt
CONTINUE_PROMPT = """براہ کرم جاری رکھیں۔"""

# Are you there?
STILL_THERE = """کیا آپ وہاں ہیں؟"""

# =============================================================================
# CLOSING (Matches Document)
# =============================================================================

CLOSING = """بہت شکریہ آپ کے وقت کا۔ آپ کے جوابات محفوظ ہو گئے ہیں۔
اگر کوئی شکایت ہو تو FOS ہیلپ لائن پر کال کریں: 0800-91299
اللہ حافظ!"""

CLOSING_SHORT = """شکریہ! آپ کے جوابات محفوظ ہو گئے۔ اللہ حافظ!"""

# =============================================================================
# OPTIONAL QUESTIONS
# =============================================================================

OPTIONAL_QUESTION = """یہ سوال اختیاری ہے۔ اگر جواب دینا نہیں چاہتے تو "آگے بڑھیں" کہیں۔"""

SKIPPING = """ٹھیک ہے، آگے بڑھتے ہیں۔"""

# =============================================================================  
# ERROR STATES
# =============================================================================

CALL_LATER = """معذرت، ابھی آپ مصروف لگ رہے ہیں۔ ہم بعد میں دوبارہ رابطہ کریں گے۔
اللہ حافظ!"""

TECHNICAL_ERROR = """معذرت، کچھ تکنیکی مسئلہ ہو گیا۔ ہم جلد دوبارہ رابطہ کریں گے۔
اللہ حافظ!"""


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_greeting(employee_name: str) -> str:
    """Format greeting with employee name"""
    return GREETING.format(employee_name=employee_name)


def format_identity_confirmed(employee_name: str) -> str:
    """Format identity confirmation"""
    return IDENTITY_CONFIRMED.format(employee_name=employee_name)


def format_question(question_number: int, question_text: str) -> str:
    """Format question prompt"""
    return ASK_QUESTION.format(
        question_number=question_number,
        question_text=question_text
    )
