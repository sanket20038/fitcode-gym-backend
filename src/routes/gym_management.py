from flask import Blueprint, request, jsonify
from src.models.gym import db, Gym, GymMachine, MultilingualContent
from src.routes.auth import token_required
import os
from werkzeug.utils import secure_filename

gym_bp = Blueprint('gym', __name__)

@gym_bp.route('/gym', methods=['POST'])
@token_required('owner')
def create_gym(current_user):
    try:
        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({'message': 'Gym name is required'}), 400

        existing_gym = Gym.query.filter_by(owner_id=current_user.id).first()
        if existing_gym:
            return jsonify({'message': 'You already have a gym registered'}), 400

        new_gym = Gym(
            owner_id=current_user.id,
            name=data['name'],
            logo_url=data.get('logo_url'),
            contact_info=data.get('contact_info')
        )

        db.session.add(new_gym)
        db.session.commit()

        return jsonify({
            'message': 'Gym created successfully',
            'gym': new_gym.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to create gym: {str(e)}'}), 500


@gym_bp.route('/gym', methods=['GET'])
@token_required('owner')
def get_gym(current_user):
    try:
        gym = Gym.query.filter_by(owner_id=current_user.id).first()
        if not gym:
            return jsonify({'message': 'No gym found for this owner'}), 404
        return jsonify({'gym': gym.to_dict()}), 200
    except Exception as e:
        return jsonify({'message': f'Failed to retrieve gym: {str(e)}'}), 500


@gym_bp.route('/gym', methods=['PUT'])
@token_required('owner')
def update_gym(current_user):
    try:
        data = request.get_json()
        gym = Gym.query.filter_by(owner_id=current_user.id).first()
        if not gym:
            return jsonify({'message': 'No gym found for this owner'}), 404

        if data.get('name'):
            gym.name = data['name']
        if 'logo_url' in data:
            gym.logo_url = data['logo_url']
        if 'contact_info' in data:
            gym.contact_info = data['contact_info']

        db.session.commit()

        return jsonify({
            'message': 'Gym updated successfully',
            'gym': gym.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to update gym: {str(e)}'}), 500


@gym_bp.route('/gym/machines', methods=['POST'])
@token_required('owner')
def create_machine(current_user):
    try:
        gym = Gym.query.filter_by(owner_id=current_user.id).first()
        if not gym:
            return jsonify({'message': 'You must create a gym first'}), 400

        name = request.form.get('name')
        safety_tips = request.form.get('safety_tips')
        usage_guide = request.form.get('usage_guide')
        video_url = request.form.get('how_to_use_video_url')
        local_video_path = request.form.get('local_video_path')

        if not name:
            return jsonify({'message': 'Machine name is required'}), 400

        # Handle uploaded video
        
        new_machine = GymMachine(
            gym_id=gym.id,
            name=name,
            how_to_use_video_url=video_url,
            local_video_path=local_video_path,
            safety_tips=safety_tips,
            usage_guide=usage_guide
        )

        db.session.add(new_machine)
        db.session.flush()

        multilingual_data = request.form.get('multilingual_content')
        if multilingual_data:
            import json
            try:
                multilingual_data = json.loads(multilingual_data)
                for content in multilingual_data:
                    if content.get('language_code'):
                        db.session.add(MultilingualContent(
                            machine_id=new_machine.id,
                            language_code=content['language_code'],
                            instruction_text=content.get('instruction_text'),
                            safety_text=content.get('safety_text')
                        ))
            except Exception as e:
                print("Invalid multilingual JSON:", e)

        db.session.commit()

        return jsonify({
            'message': 'Machine created successfully',
            'machine': new_machine.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to create machine: {str(e)}'}), 500


@gym_bp.route('/gym/machines/<int:machine_id>', methods=['PUT'])
@token_required('owner')
def update_machine(current_user, machine_id):
    try:
        gym = Gym.query.filter_by(owner_id=current_user.id).first()
        if not gym:
            return jsonify({'message': 'No gym found for this owner'}), 404

        machine = GymMachine.query.filter_by(id=machine_id, gym_id=gym.id).first()
        if not machine:
            return jsonify({'message': 'Machine not found'}), 404

        name = request.form.get('name')
        safety_tips = request.form.get('safety_tips')
        usage_guide = request.form.get('usage_guide')
        video_url = request.form.get('how_to_use_video_url')
        local_video_path = request.form.get('local_video_path')

        video = request.files.get('video')
        if video:
            filename = secure_filename(video.filename)
            upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            local_video_path = os.path.join("uploads", filename).replace("\\", "/")
            video.save(os.path.join(upload_folder, filename))

        if name:
            machine.name = name
        if video_url:
            machine.how_to_use_video_url = video_url
        if safety_tips:
            machine.safety_tips = safety_tips
        if usage_guide:
            machine.usage_guide = usage_guide
        if local_video_path:
            machine.local_video_path = local_video_path

        multilingual_data = request.form.get('multilingual_content')
        if multilingual_data:
            import json
            MultilingualContent.query.filter_by(machine_id=machine.id).delete()
            multilingual_data = json.loads(multilingual_data)
            for content in multilingual_data:
                if content.get('language_code'):
                    db.session.add(MultilingualContent(
                        machine_id=machine.id,
                        language_code=content['language_code'],
                        instruction_text=content.get('instruction_text'),
                        safety_text=content.get('safety_text')
                    ))

        db.session.commit()

        return jsonify({'message': 'Machine updated successfully', 'machine': machine.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to update machine: {str(e)}'}), 500


@gym_bp.route('/gym/machines', methods=['GET'])
@token_required('owner')
def get_machines(current_user):
    try:
        gym = Gym.query.filter_by(owner_id=current_user.id).first()
        if not gym:
            return jsonify({'message': 'No gym found for this owner'}), 404

        machines = GymMachine.query.filter_by(gym_id=gym.id).all()
        result = []
        for machine in machines:
            machine_dict = machine.to_dict()
            multilingual = MultilingualContent.query.filter_by(machine_id=machine.id).all()
            machine_dict['multilingual_content'] = [m.to_dict() for m in multilingual]
            result.append(machine_dict)

        return jsonify({'machines': result}), 200

    except Exception as e:
        return jsonify({'message': f'Failed to retrieve machines: {str(e)}'}), 500


@gym_bp.route('/gym/machines/<int:machine_id>', methods=['DELETE'])
@token_required('owner')
def delete_machine(current_user, machine_id):
    try:
        gym = Gym.query.filter_by(owner_id=current_user.id).first()
        if not gym:
            return jsonify({'message': 'No gym found for this owner'}), 404

        machine = GymMachine.query.filter_by(id=machine_id, gym_id=gym.id).first()
        if not machine:
            return jsonify({'message': 'Machine not found'}), 404

        db.session.delete(machine)
        db.session.commit()

        return jsonify({'message': 'Machine deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to delete machine: {str(e)}'}), 500
