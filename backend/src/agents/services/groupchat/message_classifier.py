"""
Message Classifier for intelligent conversation handling
"""
import re
from typing import Dict, Tuple, List

class MessageClassifier:
    """Classifies messages to determine appropriate response strategy"""
    
    # Simple greeting patterns
    GREETING_PATTERNS = [
        r'^(hi|hello|hey|ciao|salve|buongiorno|buonasera)[\s!,.*]*$',
        r'^say\s+(hi|hello|hey)[\s!,.*]*$',
        r'^(good\s+)?(morning|afternoon|evening)[\s!,.*]*$',
    ]
    
    # Simple query patterns that need quick answers
    SIMPLE_QUERIES = [
        r'^what\s+time\s+is\s+it[\s?]*$',
        r'^what\'?s?\s+your\s+name[\s?]*$',
        r'^who\s+are\s+you[\s?]*$',
        r'^(provide|give)\s+a?\s?(brief|quick|short)\s+(status|update|summary)[\s?]*$',
        r'^test[\s!,.*]*$',
    ]
    
    # Complex business patterns requiring full orchestration
    COMPLEX_PATTERNS = [
        r'strategy|strategic',
        r'plan|planning|roadmap',
        r'analyze|analysis|assessment',
        r'optimize|optimization',
        r'talent|hiring|recruitment',
        r'budget|financial|cost',
        r'process|workflow|automation',
        r'kpi|metric|performance',
        r'governance|compliance',
    ]
    
    @classmethod
    def classify_message(cls, message: str) -> Tuple[str, Dict]:
        """
        Classify a message and return type with metadata
        
        Returns:
            Tuple of (message_type, metadata)
            message_type: 'greeting', 'simple_query', 'complex_business', 'standard'
        """
        message_lower = message.lower().strip()
        
        # Check for greetings first
        for pattern in cls.GREETING_PATTERNS:
            if re.match(pattern, message_lower):
                return 'greeting', {
                    'max_turns': 1,
                    'single_agent': True,
                    'terminate_on_response': True
                }
        
        # Check for simple queries
        for pattern in cls.SIMPLE_QUERIES:
            if re.match(pattern, message_lower):
                return 'simple_query', {
                    'max_turns': 2,
                    'single_agent': True,
                    'terminate_on_response': True
                }
        
        # Check for complex business needs
        complex_count = sum(1 for pattern in cls.COMPLEX_PATTERNS 
                           if re.search(pattern, message_lower))
        
        if complex_count >= 2:
            return 'complex_business', {
                'max_turns': 10,
                'single_agent': False,
                'terminate_on_response': False
            }
        elif complex_count == 1:
            return 'standard', {
                'max_turns': 5,
                'single_agent': False,
                'terminate_on_response': False
            }
        
        # Default for unclassified
        return 'standard', {
            'max_turns': 3,
            'single_agent': False,
            'terminate_on_response': True
        }
    
    @classmethod
    def get_termination_phrases(cls, message_type: str) -> List[str]:
        """Get appropriate termination phrases for message type"""
        if message_type == 'greeting':
            return ['hello', 'hi ', 'greetings', "i'm ", "i am "]
        elif message_type == 'simple_query':
            return ['here is', 'the answer is', 'status:', 'update:']
        else:
            return ['final answer:', 'conclusion:', 'summary:', 
                   'in summary', 'to conclude', 'recommendation:']