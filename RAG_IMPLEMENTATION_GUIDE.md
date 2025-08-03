# RAG Implementation Guide: Diet PDF Integration with Chatbot

## Overview

This implementation adds Retrieval-Augmented Generation (RAG) functionality to the NutriBot chatbot, allowing it to read and understand users' diet PDFs and provide personalized nutrition advice based on their specific diet plans.

## Architecture

### Components

1. **PDF RAG Service** (`backend/services/pdf_rag_service.py`)
   - Extracts text from diet PDFs using multiple methods
   - Caches extracted text for performance
   - Handles different PDF storage formats (Firebase Storage, Firestore)

2. **Enhanced Chatbot Endpoint** (`backend/server.py`)
   - Integrates RAG service with existing chatbot
   - Enhances system prompts with diet context
   - Maintains backward compatibility

3. **Mobile App Integration** (`mobileapp/ChatbotScreen.tsx`)
   - Passes diet PDF URL to backend
   - Displays diet availability status

## Features

### PDF Text Extraction
- **Multiple Extraction Methods**: Uses both `pdfplumber` and `PyPDF2` for robust text extraction
- **Storage Format Support**: Handles Firebase Storage URLs, Firestore base64 data, and direct blob access
- **Caching**: In-memory cache for extracted text to improve performance
- **Error Handling**: Graceful fallback if PDF extraction fails

### RAG Integration
- **Context Enhancement**: Automatically enhances chatbot prompts with diet PDF content
- **Token Management**: Limits text to 4000 characters to avoid token limits
- **Personalized Responses**: Chatbot can answer questions about specific diet plans

### User Experience
- **Seamless Integration**: Works automatically when users have diet PDFs
- **Backward Compatibility**: Functions normally for users without diet PDFs
- **Real-time Updates**: Reflects latest diet PDF content

## Implementation Details

### Backend Changes

#### 1. New Dependencies
```txt
PyPDF2>=3.0.1
pdfplumber>=0.10.3
```

#### 2. PDF RAG Service
```python
class PDFRAGService:
    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> str
    def extract_text_from_firebase_url(self, url: str) -> str
    def extract_text_from_firestore(self, user_id: str, db) -> str
    def get_diet_pdf_text(self, user_id: str, diet_pdf_url: str, db) -> Optional[str]
    def create_diet_context_prompt(self, diet_text: str) -> str
    def enhance_chatbot_prompt(self, user_id: str, diet_pdf_url: str, db, base_prompt: str) -> str
```

#### 3. Enhanced Chatbot Endpoint
The `/chatbot/message` endpoint now:
- Checks for user's diet PDF URL
- Extracts text from PDF using RAG service
- Enhances system prompt with diet context
- Maintains original functionality if no PDF exists

### Frontend Changes

#### 1. Updated User Profile Interface
```typescript
export interface UserProfile {
  // ... existing fields ...
  dietPdfUrl?: string; // URL to the user's diet PDF
  lastDietUpload?: string; // Timestamp of last diet upload
  dieticianId?: string; // ID of the dietician who uploaded the diet
}
```

#### 2. Enhanced Chatbot Screen
- Displays diet PDF availability status
- Passes complete user profile to backend
- Maintains existing UI/UX

## Usage Examples

### For Users with Diet PDFs

Users can now ask questions like:
- "What should I eat for breakfast according to my diet plan?"
- "Can you tell me about my lunch options?"
- "What are my dinner recommendations?"
- "How many calories should I consume today?"
- "What snacks are allowed in my diet?"
- "Are there any foods I should avoid?"

### For Users without Diet PDFs

The chatbot continues to function normally, providing general nutrition advice based on user profiles.

## Technical Implementation

### PDF Processing Flow

1. **Detection**: Chatbot checks if user has `dietPdfUrl` in profile
2. **Retrieval**: Fetches PDF from appropriate storage location
3. **Extraction**: Uses multiple methods to extract text content
4. **Caching**: Stores extracted text in memory for future use
5. **Enhancement**: Adds diet context to chatbot system prompt
6. **Response**: Generates personalized responses using enhanced context

### Error Handling

- **PDF Not Found**: Gracefully falls back to basic prompt
- **Extraction Failure**: Logs error and continues without diet context
- **Network Issues**: Handles Firebase Storage connectivity problems
- **Token Limits**: Truncates text to stay within API limits

### Performance Optimizations

- **Caching**: Extracted text is cached to avoid repeated processing
- **Async Processing**: PDF extraction runs asynchronously
- **Selective Enhancement**: Only enhances prompts when diet PDF exists
- **Memory Management**: Limits cache size and text length

## Testing

### Test Script
Run `test_rag_functionality.py` to verify:
- PDF text extraction
- Chatbot response enhancement
- Diet-specific question handling
- Error scenarios

### Manual Testing
1. Upload a diet PDF for a user
2. Ask diet-specific questions in chatbot
3. Verify responses reference the diet plan
4. Test with users who don't have diet PDFs

## Configuration

### Environment Variables
No additional environment variables required. Uses existing Firebase configuration.

### Dependencies
Add to `backend/requirements.txt`:
```txt
PyPDF2>=3.0.1
pdfplumber>=0.10.3
```

## Security Considerations

- **PDF Validation**: Only processes PDF files from trusted sources
- **Content Limits**: Restricts text length to prevent abuse
- **Error Logging**: Logs errors without exposing sensitive content
- **Access Control**: Respects existing user authentication

## Future Enhancements

### Potential Improvements
1. **Vector Database**: Store PDF embeddings for better retrieval
2. **Semantic Search**: Find relevant sections based on questions
3. **Multi-language Support**: Extract text from PDFs in different languages
4. **OCR Integration**: Handle scanned PDFs with image content
5. **Chunking**: Split large PDFs into manageable sections

### Monitoring
- Add metrics for PDF processing success rates
- Monitor chatbot response quality with diet context
- Track user engagement with diet-specific questions

## Troubleshooting

### Common Issues

1. **PDF Extraction Fails**
   - Check if PDF is corrupted or password-protected
   - Verify Firebase Storage permissions
   - Check server logs for extraction errors

2. **Chatbot Responses Generic**
   - Verify diet PDF URL is correctly set in user profile
   - Check if PDF text extraction succeeded
   - Review system prompt enhancement

3. **Performance Issues**
   - Monitor PDF processing time
   - Check cache hit rates
   - Consider implementing background processing

### Debug Commands

```bash
# Test PDF extraction
python test_rag_functionality.py

# Check user diet status
curl http://localhost:8000/api/users/{user_id}/diet

# Test chatbot with diet context
curl -X POST http://localhost:8000/api/chatbot/message \
  -H "Content-Type: application/json" \
  -d '{"userId":"user_id","chat_history":[],"user_profile":{"dietPdfUrl":"url"},"user_message":"What should I eat for breakfast?"}'
```

## Conclusion

This RAG implementation successfully integrates diet PDF content with the chatbot, enabling personalized nutrition advice based on users' specific diet plans. The solution is robust, scalable, and maintains backward compatibility while providing significant value to users with diet PDFs. 