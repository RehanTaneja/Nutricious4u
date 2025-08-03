# Diet Notification System Guide

## Overview

The Diet Notification System automatically extracts timed activities from users' diet PDFs and converts them into scheduled push notifications. This system uses advanced text parsing and pattern recognition to identify time-based activities in diet plans and creates personalized reminders for users.

## Features

### Automatic Time Extraction
- **Multiple Time Formats**: Recognizes 12-hour and 24-hour time formats
- **Text-based Times**: Converts "morning", "breakfast", "lunch", "dinner", etc. to specific times
- **Flexible Patterns**: Handles various time notations (8:00, 8.00, 8 00, etc.)

### Activity Recognition
- **Smart Keywords**: Identifies activities using nutrition and health-related keywords
- **Context Awareness**: Extracts meaningful activity descriptions from diet text
- **Multi-language Support**: Works with diet PDFs in different languages

### Notification Management
- **Automatic Scheduling**: Creates daily recurring notifications
- **User Control**: Users can edit, delete, or test notifications
- **Integration**: Seamlessly integrates with existing notification system

## Architecture

### Components

1. **Diet Notification Service** (`backend/services/diet_notification_service.py`)
   - Extracts timed activities from diet PDF text
   - Converts activities into notification objects
   - Handles notification sending and management

2. **Enhanced Diet Upload** (`backend/server.py`)
   - Automatically extracts notifications when diet PDFs are uploaded
   - Stores extracted notifications in Firestore
   - Sends immediate notifications to users

3. **Mobile App Integration** (`mobileapp/screens.tsx`)
   - Diet notification management UI
   - Extract, test, and delete diet notifications
   - Integration with existing notification settings

### Data Flow

1. **Diet PDF Upload**: User uploads diet PDF via dietician
2. **Text Extraction**: PDF text is extracted using RAG service
3. **Time Pattern Recognition**: Service identifies timed activities
4. **Notification Creation**: Activities are converted to notification objects
5. **Storage**: Notifications are stored in Firestore
6. **User Management**: Users can manage notifications via mobile app

## Implementation Details

### Backend Services

#### Diet Notification Service
```python
class DietNotificationService:
    def extract_timed_activities(self, diet_text: str) -> List[Dict]
    def create_notification_from_activity(self, activity: Dict) -> Dict
    def extract_and_create_notifications(self, user_id: str, diet_pdf_url: str, db) -> List[Dict]
    def send_immediate_notification(self, user_id: str, notification: Dict) -> bool
```

#### API Endpoints
- `POST /users/{user_id}/diet/notifications/extract` - Extract notifications from diet PDF
- `GET /users/{user_id}/diet/notifications` - Get user's diet notifications
- `DELETE /users/{user_id}/diet/notifications/{notification_id}` - Delete specific notification
- `POST /users/{user_id}/diet/notifications/test` - Send test notification

### Frontend Integration

#### API Functions
```typescript
export const extractDietNotifications = async (userId: string)
export const getDietNotifications = async (userId: string)
export const deleteDietNotification = async (userId: string, notificationId: string)
export const testDietNotification = async (userId: string)
```

#### UI Components
- Diet notification extraction button
- List of extracted activities with time
- Test and delete functionality for each notification
- Integration with existing notification settings

## Time Pattern Recognition

### Supported Formats

#### Numeric Times
- `8:00` or `8:00 AM` → 08:00
- `2:30 PM` → 14:30
- `8.00` or `8 00` → 08:00
- `14:30` → 14:30 (24-hour format)

#### Text-based Times
- `morning`, `breakfast` → 08:00
- `noon`, `lunch` → 12:00
- `afternoon` → 15:00
- `evening`, `dinner` → 19:00
- `night`, `bedtime`, `sleep` → 22:00

### Activity Keywords
The system recognizes activities using keywords like:
- `water`, `drink`, `eat`, `meal`, `breakfast`, `lunch`, `dinner`, `snack`
- `supplement`, `vitamin`, `medicine`, `medication`
- `exercise`, `workout`, `walk`, `run`, `yoga`, `meditation`
- `sleep`, `rest`, `wake`, `wake up`, `take`, `consume`, `have`

## Usage Examples

### For Users

1. **Automatic Extraction**: When a dietician uploads a diet PDF, the system automatically extracts timed activities
2. **Manual Extraction**: Users can manually extract notifications from their diet PDF
3. **Management**: Users can view, test, and delete extracted notifications
4. **Integration**: Diet notifications appear alongside custom notifications

### For Dieticians

1. **Upload Diet PDF**: Upload diet PDF for a user
2. **Automatic Processing**: System automatically extracts timed activities
3. **User Notification**: User receives notification about new diet plan
4. **Activity Extraction**: Timed activities are automatically converted to notifications

### Example Diet PDF Content
```
Breakfast (8:00 AM): Have oatmeal with fruits and nuts
Morning (9:30): Drink 2 glasses of water
Lunch (12:30 PM): Grilled chicken salad with vegetables
Afternoon (3:00): Healthy snack - apple with peanut butter
Dinner (7:00 PM): Salmon with steamed vegetables
Bedtime (10:00): Take vitamin supplements
```

**Extracted Notifications:**
- 8:00 AM: Have oatmeal with fruits and nuts
- 9:30: Drink 2 glasses of water
- 12:30 PM: Grilled chicken salad with vegetables
- 3:00: Healthy snack - apple with peanut butter
- 7:00 PM: Salmon with steamed vegetables
- 10:00: Take vitamin supplements

## Technical Implementation

### PDF Processing
1. **Text Extraction**: Uses existing RAG service to extract text from PDF
2. **Line Processing**: Processes each line of text for time patterns
3. **Activity Extraction**: Identifies activities using keyword matching
4. **Time Conversion**: Converts various time formats to standard format

### Notification Creation
1. **Activity Validation**: Ensures extracted activities contain relevant keywords
2. **Time Validation**: Validates time format and range (00:00-23:59)
3. **Notification Object**: Creates structured notification objects
4. **Storage**: Stores notifications in Firestore with user association

### Error Handling
- **PDF Extraction Failures**: Graceful fallback if PDF text extraction fails
- **Time Parsing Errors**: Skips invalid time formats
- **Activity Recognition**: Only creates notifications for recognized activities
- **Network Issues**: Handles Firebase connectivity problems

## Testing

### Test Script
Run `test_diet_notifications.py` to verify:
- Diet PDF notification extraction
- Time pattern recognition
- Notification management operations
- Error handling scenarios

### Manual Testing
1. Upload a diet PDF with timed activities
2. Check automatic notification extraction
3. Test notification sending
4. Verify notification management in mobile app

## Configuration

### Environment Variables
No additional environment variables required. Uses existing Firebase configuration.

### Dependencies
Uses existing PDF processing libraries:
- `PyPDF2` and `pdfplumber` for text extraction
- Existing notification infrastructure

## Security Considerations

- **PDF Validation**: Only processes PDF files from trusted sources
- **User Authentication**: Respects existing user authentication
- **Data Privacy**: Notifications are user-specific and private
- **Error Logging**: Logs errors without exposing sensitive content

## Future Enhancements

### Potential Improvements
1. **Machine Learning**: Use ML for better activity recognition
2. **Natural Language Processing**: Better understanding of diet instructions
3. **Smart Scheduling**: Adaptive notification timing based on user behavior
4. **Multi-language Support**: Support for diet PDFs in different languages
5. **OCR Integration**: Handle scanned PDFs with image content

### Monitoring
- Track notification extraction success rates
- Monitor user engagement with diet notifications
- Analyze time pattern recognition accuracy
- Measure notification effectiveness

## Troubleshooting

### Common Issues

1. **No Notifications Extracted**
   - Check if diet PDF contains timed activities
   - Verify time format is supported
   - Ensure activities contain recognized keywords

2. **Incorrect Time Extraction**
   - Check time format in diet PDF
   - Verify AM/PM notation is clear
   - Review text-based time mappings

3. **Notification Not Sending**
   - Verify user has notification permissions
   - Check Firebase notification setup
   - Ensure user has valid notification token

### Debug Commands

```bash
# Test notification extraction
python test_diet_notifications.py

# Check user's diet notifications
curl http://localhost:8000/api/users/{user_id}/diet/notifications

# Extract notifications manually
curl -X POST http://localhost:8000/api/users/{user_id}/diet/notifications/extract

# Test notification sending
curl -X POST http://localhost:8000/api/users/{user_id}/diet/notifications/test
```

## Conclusion

The Diet Notification System successfully automates the process of creating personalized reminders from diet PDFs. By extracting timed activities and converting them into scheduled notifications, the system helps users follow their diet plans more effectively while maintaining full control over their notification preferences. 