import PyPDF2
import pdfplumber
import io
import base64
import requests
from typing import Optional, List, Dict
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class PDFRAGService:
    """
    Service for extracting text from PDFs and providing RAG functionality
    for the chatbot to understand diet PDFs.
    """
    
    def __init__(self):
        self.pdf_cache = {}  # Simple in-memory cache for extracted text
    
    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF bytes using multiple methods for better coverage.
        """
        try:
            # Try pdfplumber first (better for complex layouts)
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                if text.strip():
                    return text.strip()
            
            # Fallback to PyPDF2 if pdfplumber didn't extract much text
            with io.BytesIO(pdf_bytes) as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                return text.strip()
                
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise HTTPException(status_code=500, detail="Failed to extract text from PDF")
    
    def extract_text_from_firebase_url(self, url: str) -> str:
        """
        Extract text from PDF stored in Firebase Storage.
        """
        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Failed to fetch PDF from Firebase Storage")
            
            return self.extract_text_from_pdf_bytes(response.content)
            
        except Exception as e:
            logger.error(f"Error extracting text from Firebase URL: {e}")
            raise HTTPException(status_code=500, detail="Failed to extract text from PDF URL")
    
    def extract_text_from_firestore(self, user_id: str, db) -> str:
        """
        Extract text from PDF stored in Firestore as base64.
        """
        try:
            doc = db.collection("diet_pdfs").document(user_id).get()
            if not doc.exists:
                raise HTTPException(status_code=404, detail="Diet PDF not found in Firestore")
            
            data = doc.to_dict()
            pdf_data = data.get("pdf_data")
            
            if not pdf_data:
                raise HTTPException(status_code=404, detail="PDF data not found in Firestore")
            
            # Decode base64 data
            pdf_bytes = base64.b64decode(pdf_data)
            return self.extract_text_from_pdf_bytes(pdf_bytes)
            
        except Exception as e:
            logger.error(f"Error extracting text from Firestore: {e}")
            raise HTTPException(status_code=500, detail="Failed to extract text from Firestore PDF")
    
    def get_diet_pdf_text(self, user_id: str, diet_pdf_url: str, db) -> Optional[str]:
        """
        Get diet PDF text from various storage locations.
        Returns cached text if available, otherwise extracts and caches.
        """
        cache_key = f"{user_id}_{diet_pdf_url}"
        
        # Check cache first
        if cache_key in self.pdf_cache:
            return self.pdf_cache[cache_key]
        
        try:
            text = None
            
            # Handle different URL formats
            if diet_pdf_url.startswith('https://storage.googleapis.com/'):
                text = self.extract_text_from_firebase_url(diet_pdf_url)
            elif diet_pdf_url.startswith('firestore://'):
                text = self.extract_text_from_firestore(user_id, db)
            elif diet_pdf_url.endswith('.pdf'):
                # Assume it's a Firebase Storage blob
                from services.firebase_client import bucket
                blob_path = f"diets/{user_id}/{diet_pdf_url}"
                blob = bucket.blob(blob_path)
                pdf_bytes = blob.download_as_bytes()
                text = self.extract_text_from_pdf_bytes(pdf_bytes)
            else:
                logger.warning(f"Unknown diet PDF URL format: {diet_pdf_url}")
                return None
            
            # Cache the extracted text
            if text:
                self.pdf_cache[cache_key] = text
                logger.info(f"Successfully extracted and cached PDF text for user {user_id}")
            
            return text
            
        except Exception as e:
            logger.error(f"Error getting diet PDF text for user {user_id}: {e}")
            return None
    
    def create_diet_context_prompt(self, diet_text: str) -> str:
        """
        Create a context prompt from diet PDF text for the chatbot.
        """
        if not diet_text:
            return ""
        
        # Clean and format the diet text
        cleaned_text = diet_text.strip()
        
        # Limit the text to avoid token limits (keep first 4000 characters)
        if len(cleaned_text) > 4000:
            cleaned_text = cleaned_text[:4000] + "..."
        
        context_prompt = f"""
CURRENT DIET PLAN INFORMATION:
{cleaned_text}

IMPORTANT: You can now answer questions about the user's current diet plan. Use this information to provide personalized advice about their meals, nutritional requirements, and dietary recommendations. Always refer to their specific diet plan when answering questions about their nutrition.
"""
        return context_prompt.strip()
    
    def enhance_chatbot_prompt(self, user_id: str, diet_pdf_url: str, db, base_prompt: str) -> str:
        """
        Enhance the chatbot prompt with diet PDF context using RAG.
        """
        if not diet_pdf_url:
            return base_prompt
        
        try:
            diet_text = self.get_diet_pdf_text(user_id, diet_pdf_url, db)
            if diet_text:
                diet_context = self.create_diet_context_prompt(diet_text)
                enhanced_prompt = f"{base_prompt}\n\n{diet_context}"
                logger.info(f"Enhanced chatbot prompt with diet context for user {user_id}")
                return enhanced_prompt
            else:
                logger.warning(f"Could not extract diet text for user {user_id}")
                return base_prompt
                
        except Exception as e:
            logger.error(f"Error enhancing chatbot prompt with diet context: {e}")
            return base_prompt

# Global instance
pdf_rag_service = PDFRAGService() 