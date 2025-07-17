from flask import Blueprint, request, jsonify
from src.models.gym import db, BookmarkedMachine, ScanHistory, GymMachine, Gym, MultilingualContent
from src.routes.auth import token_required
from sqlalchemy import func, desc

client_bp = Blueprint('client', __name__)

@client_bp.route('/bookmarks', methods=['POST'])
@token_required('client')
def bookmark_machine(current_user):
    try:
        data = request.get_json()
        
        if not data or not data.get('machine_id'):
            return jsonify({'message': 'Machine ID is required'}), 400
        
        machine_id = data['machine_id']
        
        # Check if machine exists
        machine = GymMachine.query.get(machine_id)
        if not machine:
            return jsonify({'message': 'Machine not found'}), 404
        
        # Check if already bookmarked
        existing_bookmark = BookmarkedMachine.query.filter_by(
            client_id=current_user.id,
            machine_id=machine_id
        ).first()
        
        if existing_bookmark:
            return jsonify({'message': 'Machine already bookmarked'}), 400
        
        # Create bookmark
        new_bookmark = BookmarkedMachine(
            client_id=current_user.id,
            machine_id=machine_id
        )
        
        db.session.add(new_bookmark)
        db.session.commit()
        
        return jsonify({
            'message': 'Machine bookmarked successfully',
            'bookmark': new_bookmark.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to bookmark machine: {str(e)}'}), 500

@client_bp.route('/bookmarks', methods=['GET'])
@token_required('client')
def get_bookmarks(current_user):
    try:
        bookmarks = db.session.query(BookmarkedMachine, GymMachine, Gym).join(
            GymMachine, BookmarkedMachine.machine_id == GymMachine.id
        ).join(
            Gym, GymMachine.gym_id == Gym.id
        ).filter(
            BookmarkedMachine.client_id == current_user.id
        ).order_by(desc(BookmarkedMachine.bookmark_timestamp)).all()
        
        bookmarks_data = []
        for bookmark, machine, gym in bookmarks:
            bookmark_dict = bookmark.to_dict()
            bookmark_dict['machine'] = machine.to_dict()
            bookmark_dict['gym'] = gym.to_dict()
            bookmarks_data.append(bookmark_dict)
        
        return jsonify({'bookmarks': bookmarks_data}), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to retrieve bookmarks: {str(e)}'}), 500

@client_bp.route('/bookmarks/<int:machine_id>', methods=['DELETE'])
@token_required('client')
def remove_bookmark(current_user, machine_id):
    try:
        bookmark = BookmarkedMachine.query.filter_by(
            client_id=current_user.id,
            machine_id=machine_id
        ).first()
        
        if not bookmark:
            return jsonify({'message': 'Bookmark not found'}), 404
        
        db.session.delete(bookmark)
        db.session.commit()
        
        return jsonify({'message': 'Bookmark removed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to remove bookmark: {str(e)}'}), 500

@client_bp.route('/scan-history', methods=['GET'])
@token_required('client')
def get_scan_history(current_user):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        scan_history = db.session.query(ScanHistory, GymMachine, Gym).join(
            GymMachine, ScanHistory.machine_id == GymMachine.id
        ).join(
            Gym, GymMachine.gym_id == Gym.id
        ).filter(
            ScanHistory.client_id == current_user.id
        ).order_by(desc(ScanHistory.scan_timestamp)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        history_data = []
        for scan, machine, gym in scan_history.items:
            scan_dict = scan.to_dict()
            scan_dict['machine'] = machine.to_dict()
            scan_dict['gym'] = gym.to_dict()
            history_data.append(scan_dict)
        
        return jsonify({
            'scan_history': history_data,
            'pagination': {
                'page': scan_history.page,
                'pages': scan_history.pages,
                'per_page': scan_history.per_page,
                'total': scan_history.total,
                'has_next': scan_history.has_next,
                'has_prev': scan_history.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to retrieve scan history: {str(e)}'}), 500

@client_bp.route('/machine/<int:machine_id>', methods=['GET'])
@token_required('client')
def get_machine_details(current_user, machine_id):
    try:
        machine = GymMachine.query.get(machine_id)
        
        if not machine:
            return jsonify({'message': 'Machine not found'}), 404
        
        gym = Gym.query.get(machine.gym_id)
        
        # Get multilingual content
        multilingual_content = MultilingualContent.query.filter_by(machine_id=machine_id).all()
        
        # Check if bookmarked
        is_bookmarked = BookmarkedMachine.query.filter_by(
            client_id=current_user.id,
            machine_id=machine_id
        ).first() is not None
        
        machine_dict = machine.to_dict()
        machine_dict['gym'] = gym.to_dict() if gym else None
        machine_dict['multilingual_content'] = [content.to_dict() for content in multilingual_content]
        machine_dict['is_bookmarked'] = is_bookmarked
        
        return jsonify({'machine': machine_dict}), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to retrieve machine details: {str(e)}'}), 500

@client_bp.route('/gemini-ai', methods=['POST'])
@token_required('client')
def gemini_ai():
    try:
        data = request.get_json()
        user_input = data.get('user_input', '')
        # TODO: Integrate with Gemini AI API here
        # For now, mock the response
        processed_response = f"Gemini AI processed response based on input:\n{user_input}\n\n[This is a mocked response.]"

        return jsonify({'response': processed_response}), 200
    except Exception as e:
        return jsonify({'message': f'Failed to process Gemini AI request: {str(e)}'}), 500

