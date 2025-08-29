# Additional Flask Routes for Complete Educational Law RAG Chatbot
# This file contains the remaining API routes that complete the system

from final_complete_chatbot import app, db, complete_rag, ChatHistory, User, PDFDocument, DocumentChunk, LearningAnalytics
from flask import request, jsonify
import json
import hashlib
import time
from datetime import datetime

@app.route('/api/upload', methods=['POST'])
def upload_pdfs():
    """Enhanced PDF upload with comprehensive processing"""
    try:
        if 'pdfs' not in request.files:
            return jsonify({'success': False, 'error': 'No PDF files uploaded'})
        
        files = request.files.getlist('pdfs')
        processed_count = 0
        errors = []
        total_chunks = 0
        
        for file in files:
            if file.filename == '':
                continue
                
            if not file.filename.lower().endswith('.pdf'):
                errors.append(f"{file.filename} is not a PDF file")
                continue
            
            try:
                # Auto-detect document type
                filename_lower = file.filename.lower()
                if any(word in filename_lower for word in ['constitution', 'fundamental', 'rights', 'preamble']):
                    doc_type = 'constitution'
                elif any(word in filename_lower for word in ['law', 'penal', 'criminal', 'ipc', 'legal']):
                    doc_type = 'law'
                else:
                    doc_type = 'general'
                
                # Process PDF
                success, chunks_created = complete_rag.process_pdf_file(file, file.filename, doc_type)
                if success:
                    processed_count += 1
                    total_chunks += chunks_created
                else:
                    errors.append(f"Failed to process {file.filename}")
            except Exception as e:
                errors.append(f"Error processing {file.filename}: {str(e)}")
        
        if processed_count > 0:
            message = f"Successfully processed {processed_count} legal document(s)"
            if errors:
                message += f". Some errors occurred: {'; '.join(errors[:3])}"
            return jsonify({
                'success': True, 
                'message': message,
                'processed_count': processed_count,
                'total_chunks': total_chunks,
                'errors': errors
            })
        else:
            return jsonify({
                'success': False, 
                'error': f"No documents processed. Errors: {'; '.join(errors)}"
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/documents')
def get_documents():
    """Get all uploaded documents with processing status"""
    try:
        docs = PDFDocument.query.order_by(PDFDocument.upload_date.desc()).all()
        documents = []
        
        for doc in docs:
            chunks_count = DocumentChunk.query.filter_by(pdf_id=doc.id).count()
            documents.append({
                'id': doc.id,
                'filename': doc.filename,
                'total_pages': doc.total_pages,
                'file_size': doc.file_size,
                'upload_date': doc.upload_date.isoformat(),
                'processed': doc.processed,
                'document_type': doc.document_type,
                'chunks_created': chunks_count,
                'content_summary': doc.content_summary
            })
        
        return jsonify({'documents': documents})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/chat', methods=['POST'])
def chat():
    """Enhanced chat endpoint with comprehensive features"""
    start_time = time.time()
    
    try:
        data = request.json
        query = data.get('query', '')
        user_id = data.get('user_id', 'anonymous')
        session_id = data.get('session_id', 'default')
        age_group = data.get('age_group', 'teen')
        
        if not query.strip():
            return jsonify({'error': 'Query cannot be empty'})
        
        # Ensure user exists
        user = complete_rag.ensure_user_exists(user_id, age_group)
        user.total_questions += 1
        
        # Detect query type and scenarios
        scenario_detection = complete_rag.detect_scenario_query(query)
        query_type = scenario_detection['query_type']
        is_scenario = scenario_detection['is_scenario']
        category = scenario_detection.get('category', 'general')
        
        scenarios = []
        retrieved_docs = []
        
        if is_scenario:
            # Find relevant educational scenarios
            scenarios = complete_rag.find_relevant_scenarios(query, category)
            user.scenario_questions += 1
            
            # Also search documents for additional context
            retrieved_docs = complete_rag.search_documents(query, top_k=3)
        else:
            # Regular document search
            retrieved_docs = complete_rag.search_documents(query, top_k=5)
        
        # Generate educational response
        response, generation_score = complete_rag.generate_response(
            query, retrieved_docs, query_type, scenarios, age_group
        )
        
        # Calculate metrics
        processing_time = time.time() - start_time
        relevance_score = retrieved_docs[0]['combined_score'] if retrieved_docs else 0.0
        
        # Save to chat history
        history_entry = ChatHistory(
            user_id=user_id,
            session_id=session_id,
            query=query,
            response=response,
            query_type=query_type,
            retrieved_chunks=json.dumps([{
                'content': doc['content'][:200] + '...',
                'metadata': doc['metadata'],
                'score': doc['combined_score']
            } for doc in retrieved_docs[:3]]),
            scenario_triggered=is_scenario,
            relevance_score=relevance_score,
            processing_time=processing_time,
            user_age_group=age_group
        )
        db.session.add(history_entry)
        
        # Update learning analytics
        complete_rag.update_learning_analytics(user_id, query_type, category)
        
        db.session.commit()
        
        return jsonify({
            'response': response,
            'relevance_score': relevance_score,
            'processing_time': processing_time,
            'sources_found': len(retrieved_docs),
            'query_type': query_type,
            'scenario_triggered': is_scenario,
            'scenarios_found': len(scenarios),
            'category': category,
            'educational_focus': True,
            'age_appropriate': True
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback for self-learning improvement"""
    try:
        data = request.json
        message_id = data.get('message_id')
        score = data.get('score')  # 1 for helpful, -1 for not helpful
        user_id = data.get('user_id')
        improvement_suggestion = data.get('suggestion', '')
        
        # Find the chat history entry (simplified approach)
        # In a real system, you'd store message IDs properly
        recent_chat = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.timestamp.desc()).first()
        
        if recent_chat:
            recent_chat.feedback_score = score
            recent_chat.improvement_suggested = improvement_suggestion
            db.session.commit()
            
            # Update self-learning patterns
            complete_rag.update_response_optimization(recent_chat.query_type, score)
            
            return jsonify({'success': True, 'message': 'Feedback recorded for learning improvement'})
        else:
            return jsonify({'success': False, 'error': 'Chat history not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analytics')
def get_analytics():
    """Get comprehensive learning analytics"""
    try:
        user_id = request.args.get('user_id', 'anonymous')
        
        # User statistics
        user = User.query.get(user_id)
        user_stats = {}
        
        if user:
            total_chats = ChatHistory.query.filter_by(user_id=user_id).count()
            scenario_chats = ChatHistory.query.filter_by(user_id=user_id, scenario_triggered=True).count()
            days_active = (datetime.utcnow() - user.created_date).days + 1
            
            user_stats = {
                'total_questions': total_chats,
                'scenario_questions': scenario_chats,
                'days_active': days_active,
                'age_group': user.age_group,
                'member_since': user.created_date.strftime('%Y-%m-%d')
            }
        
        # Recent learning topics
        recent_chats = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.timestamp.desc()).limit(10).all()
        recent_topics = []
        for chat in recent_chats:
            if chat.query_type == 'legal_scenario':
                recent_topics.append(f"Scenario: {chat.query[:50]}...")
            else:
                recent_topics.append(f"General: {chat.query[:50]}...")
        
        # System-wide analytics
        total_docs = PDFDocument.query.count()
        total_chunks = DocumentChunk.query.count()
        total_users = User.query.count()
        total_scenarios = complete_rag.get_scenario_count()
        
        return jsonify({
            'user_stats': user_stats,
            'recent_topics': recent_topics,
            'system_stats': {
                'total_documents': total_docs,
                'total_chunks': total_chunks,
                'total_users': total_users,
                'educational_scenarios': total_scenarios,
                'system_status': 'Educational Law RAG System Active'
            },
            'learning_progress': complete_rag.get_learning_progress(user_id)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/history')
def get_chat_history():
    """Get user's chat history for review and learning"""
    try:
        user_id = request.args.get('user_id', 'anonymous')
        session_id = request.args.get('session_id')
        limit = int(request.args.get('limit', 20))
        
        query = ChatHistory.query.filter_by(user_id=user_id)
        if session_id:
            query = query.filter_by(session_id=session_id)
        
        history = query.order_by(ChatHistory.timestamp.desc()).limit(limit).all()
        
        history_data = []
        for chat in history:
            history_data.append({
                'id': chat.id,
                'query': chat.query,
                'response': chat.response[:500] + '...' if len(chat.response) > 500 else chat.response,
                'query_type': chat.query_type,
                'scenario_triggered': chat.scenario_triggered,
                'timestamp': chat.timestamp.isoformat(),
                'relevance_score': chat.relevance_score,
                'feedback_score': chat.feedback_score
            })
        
        return jsonify({
            'history': history_data,
            'total_count': len(history_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/scenarios')
def get_available_scenarios():
    """Get all available educational scenarios"""
    try:
        age_group = request.args.get('age_group', 'teen')
        category = request.args.get('category')
        
        query = complete_rag.ScenarioCase.query
        
        if age_group != 'all':
            query = query.filter_by(age_group=age_group)
        
        if category:
            query = query.filter_by(category=category)
        
        scenarios = query.all()
        
        scenario_data = []
        for scenario in scenarios:
            scenario_data.append({
                'id': scenario.id,
                'title': scenario.scenario_title,
                'description': scenario.scenario_description,
                'category': scenario.category,
                'age_group': scenario.age_group,
                'severity_level': scenario.severity_level,
                'keywords': scenario.keywords
            })
        
        return jsonify({
            'scenarios': scenario_data,
            'categories': complete_rag.get_scenario_categories(),
            'total_count': len(scenario_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/search', methods=['POST'])
def advanced_search():
    """Advanced search across documents with filters"""
    try:
        data = request.json
        query = data.get('query', '')
        document_types = data.get('document_types', [])
        content_types = data.get('content_types', [])
        top_k = int(data.get('top_k', 10))
        
        if not query.strip():
            return jsonify({'error': 'Query cannot be empty'})
        
        # Perform search with filters
        results = complete_rag.search_documents_with_filters(
            query, top_k, document_types, content_types
        )
        
        search_results = []
        for result in results:
            search_results.append({
                'content': result['content'][:300] + '...' if len(result['content']) > 300 else result['content'],
                'metadata': result['metadata'],
                'score': result['combined_score'],
                'source_file': result['metadata'].get('filename', 'Unknown'),
                'page_number': result['metadata'].get('page_number', 'Unknown'),
                'content_type': result['metadata'].get('content_type', 'general')
            })
        
        return jsonify({
            'results': search_results,
            'total_found': len(search_results),
            'query': query
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/system/status')
def get_system_status():
    """Get comprehensive system status"""
    try:
        status = {
            'system_name': 'Complete Educational Law & Constitution RAG Chatbot',
            'version': '1.0.0',
            'status': 'Active',
            'educational_focus': True,
            'models': {
                'embeddings': 'all-MiniLM-L6-v2',
                'generation': 'GPT-2 + Educational Templates',
                'search_methods': ['FAISS Vector Search', 'BM25 Keyword Search', 'TF-IDF Statistical Search']
            },
            'features': {
                'pdf_processing': True,
                'scenario_learning': True,
                'age_appropriate_responses': True,
                'search_history': True,
                'self_learning': True,
                'analytics': True,
                'feedback_system': True
            },
            'database_stats': {
                'total_documents': PDFDocument.query.count(),
                'total_chunks': DocumentChunk.query.count(),
                'total_users': User.query.count(),
                'total_chats': ChatHistory.query.count(),
                'educational_scenarios': complete_rag.get_scenario_count()
            },
            'safety_features': {
                'educational_disclaimers': True,
                'age_appropriate_filtering': True,
                'no_illegal_promotion': True,
                'professional_guidance_recommendation': True,
                'positive_learning_focus': True
            }
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)})

# Additional utility routes
@app.route('/api/export/history', methods=['POST'])
def export_user_history():
    """Export user's learning history for teachers/parents"""
    try:
        data = request.json
        user_id = data.get('user_id')
        format_type = data.get('format', 'json')  # json, summary
        
        if not user_id:
            return jsonify({'error': 'User ID required'})
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'})
        
        history = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.timestamp.desc()).all()
        
        if format_type == 'summary':
            # Generate educational summary
            summary = complete_rag.generate_learning_summary(user, history)
            return jsonify({
                'user_summary': summary,
                'export_date': datetime.utcnow().isoformat(),
                'total_interactions': len(history)
            })
        else:
            # Full history export
            history_data = []
            for chat in history:
                history_data.append({
                    'date': chat.timestamp.isoformat(),
                    'question': chat.query,
                    'type': chat.query_type,
                    'scenario_based': chat.scenario_triggered,
                    'age_group': chat.user_age_group
                })
            
            return jsonify({
                'user_id': user_id,
                'learning_history': history_data,
                'export_date': datetime.utcnow().isoformat(),
                'user_info': {
                    'age_group': user.age_group,
                    'member_since': user.created_date.isoformat(),
                    'total_questions': len(history_data)
                }
            })
            
    except Exception as e:
        return jsonify({'error': str(e)})