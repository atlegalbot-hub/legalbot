# Additional Methods for Complete Educational Law RAG Chatbot
# This file contains the remaining methods that complete the CompleteLawEducationRAG class

import numpy as np
import hashlib
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import json
import logging

logger = logging.getLogger(__name__)

# These methods should be added to the CompleteLawEducationRAG class in final_complete_chatbot.py

def chunk_text_intelligently(self, page_content: List[Dict], chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
    """Advanced intelligent text chunking for legal documents"""
    chunks = []
    
    for page_data in page_content:
        page_num = page_data['page']
        text = page_data['text']
        
        # Classify content type for better chunking
        content_type = self._classify_legal_content(text)
        
        # Split into sentences with enhanced sentence detection
        try:
            sentences = self._enhanced_sentence_tokenize(text)
        except:
            sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            # Check if adding this sentence would exceed chunk size
            if current_length + sentence_words > chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'content': chunk_text,
                    'page_number': page_num,
                    'chunk_index': len(chunks),
                    'word_count': current_length,
                    'sentences': len(current_chunk),
                    'content_type': content_type,
                    'importance_score': self._calculate_content_importance(chunk_text)
                })
                
                # Handle overlap intelligently
                if overlap > 0 and len(current_chunk) > 1:
                    overlap_sentences = current_chunk[-(overlap//50):] if overlap//50 > 0 else []
                    current_chunk = overlap_sentences + [sentence]
                    current_length = sum(len(s.split()) for s in current_chunk)
                else:
                    current_chunk = [sentence]
                    current_length = sentence_words
            else:
                current_chunk.append(sentence)
                current_length += sentence_words
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'content': chunk_text,
                'page_number': page_num,
                'chunk_index': len(chunks),
                'word_count': current_length,
                'sentences': len(current_chunk),
                'content_type': content_type,
                'importance_score': self._calculate_content_importance(chunk_text)
            })
    
    return chunks

def _enhanced_sentence_tokenize(self, text: str) -> List[str]:
    """Enhanced sentence tokenization for legal text"""
    try:
        from nltk.tokenize import sent_tokenize
        sentences = sent_tokenize(text)
        
        # Post-process to handle legal text patterns
        processed_sentences = []
        for sentence in sentences:
            # Handle section numbers and legal citations
            if len(sentence.strip()) < 10:  # Very short sentences
                if processed_sentences:
                    processed_sentences[-1] += ' ' + sentence
                else:
                    processed_sentences.append(sentence)
            else:
                processed_sentences.append(sentence)
        
        return processed_sentences
    except:
        # Fallback method
        return [s.strip() for s in text.split('.') if s.strip() and len(s.strip()) > 10]

def _classify_legal_content(self, text: str) -> str:
    """Enhanced legal content classification"""
    text_lower = text.lower()
    
    # Constitutional content
    if any(word in text_lower for word in ['fundamental right', 'article', 'constitution', 'preamble', 'directive principle']):
        return 'constitutional'
    
    # Punishment and penalties
    elif any(word in text_lower for word in ['punishment', 'penalty', 'fine', 'imprisonment', 'jail', 'sentence']):
        return 'punishment'
    
    # Rights and freedoms
    elif any(word in text_lower for word in ['right to', 'freedom of', 'liberty', 'equality', 'justice']):
        return 'rights'
    
    # Legal procedures
    elif any(word in text_lower for word in ['procedure', 'process', 'court', 'trial', 'hearing', 'appeal']):
        return 'procedure'
    
    # Specific laws and acts
    elif any(word in text_lower for word in ['section', 'ipc', 'penal code', 'act', 'law', 'provision']):
        return 'law'
    
    # Educational content
    elif any(word in text_lower for word in ['education', 'school', 'student', 'child', 'juvenile']):
        return 'educational'
    
    else:
        return 'general'

def _calculate_content_importance(self, text: str) -> float:
    """Calculate importance score for content prioritization"""
    text_lower = text.lower()
    importance_score = 0.0
    
    # High importance keywords
    high_importance = ['fundamental', 'constitution', 'right', 'law', 'section', 'article', 'punishment', 'penalty']
    for keyword in high_importance:
        importance_score += text_lower.count(keyword) * 0.3
    
    # Medium importance keywords
    medium_importance = ['procedure', 'court', 'legal', 'act', 'provision', 'justice']
    for keyword in medium_importance:
        importance_score += text_lower.count(keyword) * 0.2
    
    # Educational keywords
    educational = ['student', 'child', 'education', 'learning', 'school']
    for keyword in educational:
        importance_score += text_lower.count(keyword) * 0.25
    
    # Normalize by text length
    importance_score = min(importance_score / (len(text.split()) / 100), 1.0)
    
    return importance_score

def process_pdf_file(self, pdf_file, filename: str, document_type: str = 'general') -> Tuple[bool, int]:
    """Enhanced PDF processing with comprehensive error handling"""
    try:
        # Calculate file hash for duplicate detection
        pdf_file.seek(0)
        file_content = pdf_file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        pdf_file.seek(0)
        
        # Check if already processed
        existing_doc = PDFDocument.query.filter_by(file_hash=file_hash).first()
        if existing_doc:
            logger.info(f"📄 PDF {filename} already processed")
            existing_chunks = DocumentChunk.query.filter_by(pdf_id=existing_doc.id).count()
            return True, existing_chunks
        
        # Extract text from PDF
        logger.info(f"🔍 Extracting text from {filename}...")
        page_content, metadata = self.extract_text_from_pdf(pdf_file)
        
        if not page_content:
            logger.error(f"❌ No text extracted from {filename}")
            return False, 0
        
        # Auto-detect document type if not specified
        if document_type == 'general':
            document_type = self._detect_document_type(page_content)
        
        # Generate content summary
        content_summary = self._generate_content_summary(page_content)
        
        # Save PDF document record
        pdf_doc = PDFDocument(
            filename=filename,
            file_hash=file_hash,
            total_pages=metadata.get('total_pages', 0),
            file_size=len(file_content),
            document_type=document_type,
            content_summary=content_summary,
            processed=False
        )
        db.session.add(pdf_doc)
        db.session.commit()
        
        # Intelligent text chunking
        logger.info(f"✂️ Chunking text from {filename}...")
        chunks = self.chunk_text_intelligently(page_content, chunk_size=400, overlap=50)
        
        # Process chunks and create embeddings
        logger.info(f"🧠 Creating embeddings for {len(chunks)} chunks...")
        chunks_created = 0
        
        for chunk in chunks:
            try:
                # Generate embedding
                embedding = self.embedding_model.encode(chunk['content'])
                
                # Save chunk to database
                db_chunk = DocumentChunk(
                    pdf_id=pdf_doc.id,
                    chunk_index=chunk['chunk_index'],
                    content=chunk['content'],
                    page_number=chunk['page_number'],
                    embedding_vector=embedding.tolist(),
                    metadata=chunk,
                    content_type=chunk.get('content_type', 'general')
                )
                db.session.add(db_chunk)
                
                # Add to FAISS index
                self.faiss_index.add(embedding.reshape(1, -1).astype('float32'))
                
                # Store for other search methods
                self.documents.append(chunk['content'])
                self.document_metadata.append({
                    'chunk_id': db_chunk.id if hasattr(db_chunk, 'id') else len(self.documents) - 1,
                    'pdf_id': pdf_doc.id,
                    'filename': filename,
                    'page_number': chunk['page_number'],
                    'chunk_index': chunk['chunk_index'],
                    'content_type': chunk.get('content_type', 'general'),
                    'document_type': document_type,
                    'importance_score': chunk.get('importance_score', 0.5)
                })
                
                chunks_created += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing chunk {chunk['chunk_index']}: {e}")
        
        # Update processed status
        pdf_doc.processed = True
        db.session.commit()
        
        # Rebuild search indexes
        self._rebuild_search_indexes()
        
        logger.info(f"✅ Successfully processed {filename} with {chunks_created} chunks")
        return True, chunks_created
        
    except Exception as e:
        logger.error(f"❌ Error processing PDF {filename}: {e}")
        db.session.rollback()
        return False, 0

def _detect_document_type(self, page_content: List[Dict]) -> str:
    """Enhanced document type detection"""
    all_text = " ".join([page['text'] for page in page_content]).lower()
    
    # Constitutional documents
    if any(term in all_text for term in ['constitution of india', 'fundamental rights', 'directive principles', 'preamble']):
        return 'constitution'
    
    # Legal codes and acts
    elif any(term in all_text for term in ['indian penal code', 'ipc', 'criminal procedure', 'civil procedure', 'evidence act']):
        return 'law'
    
    # Educational materials
    elif any(term in all_text for term in ['civics', 'political science', 'legal studies', 'class', 'grade', 'student']):
        return 'educational'
    
    else:
        return 'general'

def _generate_content_summary(self, page_content: List[Dict]) -> str:
    """Generate a brief summary of document content"""
    all_text = " ".join([page['text'][:200] for page in page_content[:5]])  # First 5 pages, 200 chars each
    
    # Extract key topics
    text_lower = all_text.lower()
    topics = []
    
    if 'constitution' in text_lower:
        topics.append('Constitutional Law')
    if 'fundamental rights' in text_lower:
        topics.append('Fundamental Rights')
    if 'penal code' in text_lower or 'criminal' in text_lower:
        topics.append('Criminal Law')
    if 'procedure' in text_lower:
        topics.append('Legal Procedure')
    if 'education' in text_lower or 'student' in text_lower:
        topics.append('Educational Content')
    
    if not topics:
        topics = ['General Legal Content']
    
    return f"Topics: {', '.join(topics[:3])}. Pages: {len(page_content)}"

def search_documents(self, query: str, top_k: int = 5, content_type: str = None) -> List[Dict]:
    """Enhanced multi-method document search with improved scoring"""
    if not self.documents:
        return []
    
    results = []
    
    # 1. Semantic search with FAISS
    try:
        query_embedding = self.embedding_model.encode(query).astype('float32')
        semantic_scores, semantic_indices = self.faiss_index.search(
            query_embedding.reshape(1, -1), min(top_k * 3, len(self.documents))
        )
        
        for score, idx in zip(semantic_scores[0], semantic_indices[0]):
            if idx < len(self.documents) and score > 0:
                metadata = self.document_metadata[idx]
                
                # Apply content type filter
                if content_type and metadata.get('content_type') != content_type:
                    continue
                
                results.append({
                    'content': self.documents[idx],
                    'metadata': metadata,
                    'semantic_score': float(score),
                    'index': idx
                })
    except Exception as e:
        logger.error(f"❌ Semantic search error: {e}")
    
    # 2. Keyword search with BM25
    try:
        if self.bm25 and results:
            query_tokens = query.lower().split()
            bm25_scores = self.bm25.get_scores(query_tokens)
            
            for result in results:
                idx = result['index']
                if idx < len(bm25_scores):
                    result['bm25_score'] = float(bm25_scores[idx])
                else:
                    result['bm25_score'] = 0.0
    except Exception as e:
        logger.error(f"❌ BM25 search error: {e}")
    
    # 3. TF-IDF search
    try:
        if self.tfidf_matrix is not None and results:
            query_vector = self.tfidf_vectorizer.transform([query])
            tfidf_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            for result in results:
                idx = result['index']
                if idx < len(tfidf_scores):
                    result['tfidf_score'] = float(tfidf_scores[idx])
                else:
                    result['tfidf_score'] = 0.0
    except Exception as e:
        logger.error(f"❌ TF-IDF search error: {e}")
    
    # Enhanced score combination with importance weighting
    for result in results:
        semantic = result.get('semantic_score', 0)
        bm25 = result.get('bm25_score', 0)
        tfidf = result.get('tfidf_score', 0)
        importance = result['metadata'].get('importance_score', 0.5)
        
        # Normalize BM25 score
        max_bm25 = max([r.get('bm25_score', 0) for r in results]) if results else 1
        bm25_norm = bm25 / max_bm25 if max_bm25 > 0 else 0
        
        # Enhanced combined score with importance weighting
        base_score = 0.5 * semantic + 0.3 * bm25_norm + 0.2 * tfidf
        result['combined_score'] = base_score * (1 + 0.2 * importance)  # Boost important content
    
    # Sort by combined score and return top_k
    results.sort(key=lambda x: x['combined_score'], reverse=True)
    return results[:top_k]

def search_documents_with_filters(self, query: str, top_k: int, document_types: List[str], content_types: List[str]) -> List[Dict]:
    """Advanced search with multiple filters"""
    if not self.documents:
        return []
    
    # Get all results first
    all_results = self.search_documents(query, top_k * 2)  # Get more to allow for filtering
    
    # Apply filters
    filtered_results = []
    for result in all_results:
        metadata = result['metadata']
        
        # Document type filter
        if document_types and metadata.get('document_type') not in document_types:
            continue
        
        # Content type filter
        if content_types and metadata.get('content_type') not in content_types:
            continue
        
        filtered_results.append(result)
    
    return filtered_results[:top_k]

def generate_response(self, query: str, retrieved_docs: List[Dict], query_type: str = 'general', scenarios: List[Dict] = None, user_age: str = "teen") -> Tuple[str, float]:
    """Enhanced response generation with multiple fallback strategies"""
    
    # Scenario-based response
    if query_type == 'legal_scenario' and scenarios:
        return self.generate_scenario_response(query, scenarios, user_age), 0.9
    
    # No documents found
    if not retrieved_docs:
        if query_type == 'legal_scenario':
            return self.generate_scenario_response(query, [], user_age), 0.7
        else:
            return self._generate_fallback_response(query, user_age), 0.5
    
    # Document-based response
    try:
        # Try neural generation first
        if self.generation_model:
            neural_response = self._generate_neural_response(query, retrieved_docs, user_age)
            if neural_response and len(neural_response.strip()) > 50:
                return neural_response, 0.85
    except Exception as e:
        logger.warning(f"⚠️ Neural generation failed: {e}")
    
    # Fallback to template-based response
    template_response = self._generate_template_response(query, retrieved_docs, query_type, user_age)
    return template_response, 0.8

def _generate_neural_response(self, query: str, docs: List[Dict], user_age: str) -> str:
    """Generate response using neural model with educational focus"""
    try:
        # Prepare context from top documents
        context = self._prepare_context_for_generation(docs[:2], user_age)
        
        # Create educational prompt
        prompt = self._create_educational_prompt(query, context, user_age)
        
        # Generate with the model
        inputs = self.generation_tokenizer.encode(prompt, return_tensors='pt', max_length=512, truncation=True)
        
        with torch.no_grad():
            outputs = self.generation_model.generate(
                inputs,
                max_length=inputs.shape[1] + 200,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.generation_tokenizer.eos_token_id,
                no_repeat_ngram_size=3
            )
        
        generated_text = self.generation_tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated part
        response = generated_text[len(prompt):].strip()
        
        # Post-process for educational appropriateness
        response = self._post_process_educational_response(response, user_age)
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Neural generation error: {e}")
        return None

def _prepare_context_for_generation(self, docs: List[Dict], user_age: str) -> str:
    """Prepare educational context for generation"""
    context_parts = []
    
    for i, doc in enumerate(docs):
        metadata = doc['metadata']
        content = doc['content'][:300]  # Limit length
        
        context_parts.append(f"Source {i+1}: {content}")
    
    return " ".join(context_parts)

def _create_educational_prompt(self, query: str, context: str, user_age: str) -> str:
    """Create educational prompt for generation"""
    age_guidance = {
        'child': 'in simple, child-friendly language focusing on basic understanding',
        'teen': 'in clear language appropriate for teenagers, focusing on consequences and choices',
        'adult': 'with comprehensive information and full legal implications'
    }
    
    prompt = f"""Educational Legal Information:

Context: {context}

Question: {query}

Please provide an educational answer {age_guidance.get(user_age, 'appropriately')} that:
- Focuses on learning and understanding
- Explains laws and rights clearly
- Emphasizes positive choices and civic responsibility
- Includes educational disclaimers
- Is safe and appropriate for students

Educational Response:"""
    
    return prompt

def _post_process_educational_response(self, response: str, user_age: str) -> str:
    """Post-process response for educational appropriateness"""
    # Add educational header
    processed = "📚 **Educational Information**\n\n"
    
    # Clean up the response
    response = response.replace('\n\n\n', '\n\n').strip()
    
    # Add age-appropriate guidance
    if user_age == 'child':
        processed += "👶 **For Young Students**: " + response + "\n\n"
        processed += "Remember: This is for learning only. Always ask parents or teachers if you have questions."
    elif user_age == 'teen':
        processed += "👦👧 **For Teenagers**: " + response + "\n\n"
        processed += "Remember: Understanding laws helps you make better choices. This is educational information only."
    else:
        processed += response + "\n\n"
        processed += "Note: This is educational information. Consult legal professionals for real situations."
    
    return processed

def _generate_template_response(self, query: str, docs: List[Dict], query_type: str, user_age: str) -> str:
    """Generate template-based educational response"""
    context = self._prepare_context(docs[:3])
    key_info = self._extract_key_information(context, query)
    
    # Educational response template
    response = "📚 **Educational Legal Information**\n\n"
    
    # Add educational warning
    response += "⚠️ **Educational Purpose Only**: This information is provided for learning about laws and legal concepts. Always consult legal professionals for real legal situations.\n\n"
    
    # Main content
    response += "📖 **Based on your uploaded documents:**\n\n"
    response += key_info + "\n\n"
    
    # Add sources
    if docs:
        response += "📚 **Sources from Your Documents:**\n"
        for i, doc in enumerate(docs[:3]):
            metadata = doc['metadata']
            filename = metadata.get('filename', 'Unknown')
            page = metadata.get('page_number', 'Unknown')
            content_type = metadata.get('content_type', 'general')
            response += f"• {filename} (Page {page}) - {content_type.title()} Content\n"
        response += "\n"
    
    # Age-appropriate guidance
    if user_age == "child":
        response += "👶 **For Young Students**: Laws are like rules that help everyone get along safely. Always ask trusted adults when you have questions.\n\n"
    elif user_age == "teen":
        response += "👦👧 **For Teenagers**: Understanding laws helps you make good choices and be a responsible citizen. Your actions matter and have consequences.\n\n"
    
    # Educational conclusion
    response += "🎓 **Educational Takeaway**: Learning about laws and rights helps you become a responsible citizen who contributes positively to society!"
    
    return response

# Additional utility methods

def update_learning_analytics(self, user_id: str, query_type: str, category: str):
    """Update learning analytics for self-improvement"""
    try:
        # Find or create learning analytics entry
        analytics = LearningAnalytics.query.filter_by(
            user_id=user_id, 
            learning_topic=category
        ).first()
        
        if analytics:
            analytics.questions_asked += 1
            analytics.last_interaction = datetime.utcnow()
        else:
            analytics = LearningAnalytics(
                user_id=user_id,
                learning_topic=category,
                questions_asked=1,
                last_interaction=datetime.utcnow()
            )
            db.session.add(analytics)
        
        db.session.commit()
        
    except Exception as e:
        logger.error(f"❌ Error updating learning analytics: {e}")

def update_response_optimization(self, query_type: str, feedback_score: int):
    """Update response optimization based on feedback"""
    try:
        if query_type not in self.response_optimization:
            self.response_optimization[query_type] = {
                'total_feedback': 0,
                'positive_feedback': 0,
                'average_score': 0.0
            }
        
        self.response_optimization[query_type]['total_feedback'] += 1
        if feedback_score > 0:
            self.response_optimization[query_type]['positive_feedback'] += 1
        
        # Calculate average
        total = self.response_optimization[query_type]['total_feedback']
        positive = self.response_optimization[query_type]['positive_feedback']
        self.response_optimization[query_type]['average_score'] = positive / total if total > 0 else 0.0
        
        logger.info(f"📊 Updated optimization for {query_type}: {self.response_optimization[query_type]}")
        
    except Exception as e:
        logger.error(f"❌ Error updating response optimization: {e}")

def get_scenario_count(self) -> int:
    """Get total number of educational scenarios"""
    try:
        from final_complete_chatbot import ScenarioCase
        return ScenarioCase.query.count()
    except:
        return 8  # Default count

def get_scenario_categories(self) -> List[str]:
    """Get all available scenario categories"""
    try:
        from final_complete_chatbot import ScenarioCase
        categories = db.session.query(ScenarioCase.category).distinct().all()
        return [cat[0] for cat in categories]
    except:
        return ['property_theft', 'cybercrime', 'traffic_violation', 'vandalism', 'privacy_violation', 'academic_dishonesty', 'substance_abuse']

def get_learning_progress(self, user_id: str) -> Dict:
    """Get user's learning progress"""
    try:
        analytics = LearningAnalytics.query.filter_by(user_id=user_id).all()
        
        progress = {
            'topics_explored': len(analytics),
            'total_questions': sum(a.questions_asked for a in analytics),
            'active_days': len(set(a.last_interaction.date() for a in analytics)),
            'favorite_topic': max(analytics, key=lambda x: x.questions_asked).learning_topic if analytics else None
        }
        
        return progress
        
    except Exception as e:
        logger.error(f"❌ Error getting learning progress: {e}")
        return {'topics_explored': 0, 'total_questions': 0, 'active_days': 0, 'favorite_topic': None}

def generate_learning_summary(self, user: 'User', history: List['ChatHistory']) -> str:
    """Generate educational learning summary for teachers/parents"""
    try:
        summary = f"📊 Learning Summary for User {user.id}\n\n"
        summary += f"👤 Age Group: {user.age_group.title()}\n"
        summary += f"📅 Learning Period: {user.created_date.strftime('%Y-%m-%d')} to {datetime.utcnow().strftime('%Y-%m-%d')}\n"
        summary += f"📝 Total Questions: {len(history)}\n\n"
        
        # Analyze question types
        scenario_questions = [h for h in history if h.scenario_triggered]
        general_questions = [h for h in history if not h.scenario_triggered]
        
        summary += f"🎭 Scenario-Based Learning: {len(scenario_questions)} questions\n"
        summary += f"📚 General Legal Questions: {len(general_questions)} questions\n\n"
        
        # Most asked topics
        topics = {}
        for chat in history:
            if chat.query_type in topics:
                topics[chat.query_type] += 1
            else:
                topics[chat.query_type] = 1
        
        if topics:
            summary += "🏆 Most Explored Topics:\n"
            sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
            for topic, count in sorted_topics[:3]:
                summary += f"• {topic.replace('_', ' ').title()}: {count} questions\n"
        
        summary += "\n🎓 This shows active engagement with legal education and responsible learning!"
        
        return summary
        
    except Exception as e:
        logger.error(f"❌ Error generating learning summary: {e}")
        return "Error generating summary"