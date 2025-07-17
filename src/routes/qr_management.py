from flask import Blueprint, request, jsonify, send_file
import qrcode
import io
import base64
import secrets
import json
import os
from cryptography.fernet import Fernet
from src.models.gym import db, QRCode, GymMachine, Gym, ScanHistory
from src.routes.auth import token_required
from PIL import Image, ImageDraw, ImageFont
import requests

qr_bp = Blueprint('qr', __name__)

def get_cipher_suite():
    encryption_key = os.getenv('QR_ENCRYPTION_KEY')
    if not encryption_key:
        raise RuntimeError("QR_ENCRYPTION_KEY environment variable not set")
    return Fernet(encryption_key.encode())


@qr_bp.route('/qr/generate/<int:machine_id>', methods=['POST'])
@token_required('owner')
def generate_qr_code(current_user, machine_id):
    try:
        cipher_suite = get_cipher_suite()  # Added to define cipher_suite
        gym = Gym.query.filter_by(owner_id=current_user.id).first()
        
        if not gym:
            return jsonify({'message': 'No gym found for this owner'}), 404
        
        machine = GymMachine.query.filter_by(id=machine_id, gym_id=gym.id).first()
        
        if not machine:
            return jsonify({'message': 'Machine not found'}), 404
        
        # Check if QR code already exists
        existing_qr = QRCode.query.filter_by(machine_id=machine_id).first()
        if existing_qr:
            return jsonify({'message': 'QR code already exists for this machine', 'qr_code': existing_qr.to_dict()}), 200
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Create encrypted data
        qr_data = {
            'machine_id': machine_id,
            'gym_id': gym.id,
            'token': token,
            'platform': 'fitcode'
        }
        
        encrypted_data = cipher_suite.encrypt(json.dumps(qr_data).encode())
        
        # Create QR code record
        new_qr = QRCode(
            machine_id=machine_id,
            qr_code_data=base64.b64encode(encrypted_data).decode(),
            token=token
        )
        
        db.session.add(new_qr)
        db.session.commit()
        
        return jsonify({
            'message': 'QR code generated successfully',
            'qr_code': new_qr.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Failed to generate QR code: {e}")  # Added logging
        return jsonify({'message': f'Failed to generate QR code: {str(e)}'}), 500

@qr_bp.route('/qr/image/<int:machine_id>', methods=['GET'])
@token_required('owner')
def get_qr_image(current_user, machine_id):
    try:
        gym = Gym.query.filter_by(owner_id=current_user.id).first()
        
        if not gym:
            return jsonify({'message': 'No gym found for this owner'}), 404
        
        machine = GymMachine.query.filter_by(id=machine_id, gym_id=gym.id).first()
        
        if not machine:
            return jsonify({'message': 'Machine not found'}), 404
        
        qr_code_record = QRCode.query.filter_by(machine_id=machine_id).first()
        
        if not qr_code_record:
            return jsonify({'message': 'QR code not found for this machine'}), 404
        
        # Create QR code image with the token (this is what gets scanned)
        qr_content = qr_code_record.token
        
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=12,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="#1E40AF", back_color="white").convert("RGB")
        
        draw = ImageDraw.Draw(img)
        
        # Load gym logo from URL if available
        logo_img = None
        if gym.logo_url:
            try:
                response = requests.get(gym.logo_url)
                logo_img = Image.open(io.BytesIO(response.content))
                # Resize logo to fit on QR code
                max_logo_size = 80
                logo_img.thumbnail((max_logo_size, max_logo_size), Image.ANTIALIAS)
                # Make logo circular with white border
                mask = Image.new("L", logo_img.size, 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse((0, 0) + logo_img.size, fill=255)
                logo_img.putalpha(mask)
                border_size = 4
                border = Image.new("RGBA", (logo_img.size[0] + border_size*2, logo_img.size[1] + border_size*2), (255,255,255,255))
                border.paste(logo_img, (border_size, border_size), logo_img)
                logo_img = border
            except Exception as e:
                print(f"Failed to load gym logo: {e}")
        
        # Calculate positions
        img_w, img_h = img.size
        
        # Paste logo at center
        if logo_img:
            logo_w, logo_h = logo_img.size
            pos = ((img_w - logo_w) // 2, (img_h - logo_h) // 2)
            img.paste(logo_img, pos, mask=logo_img)
        
        # Prepare font
        try:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            font = ImageFont.truetype(font_path, 40)
        except Exception:
            font = ImageFont.load_default()
        
        # Draw gym name and machine name at top with bigger font, no shadow
        gym_name = gym.name or ""
        machine_name = machine.name or ""
        combined_text = f"{gym_name} - {machine_name}"
        text_w, text_h = draw.textsize(combined_text, font=font)
        x = (img_w - text_w) // 2
        y = 20
        # No shadow, just text
        draw.text((x, y), combined_text, font=font, fill="#1E40AF")
        
        # Add decorative border
        border_color = "#1E40AF"
        border_width = 10
        for i in range(border_width):
            draw.rectangle([i, i, img_w - i - 1, img_h - i - 1], outline=border_color)
        
        # Increase gym logo size
        logo_img = None
        if gym.logo_url:
            try:
                response = requests.get(gym.logo_url)
                logo_img = Image.open(io.BytesIO(response.content))
                # Resize logo to fit on QR code, increased size
                max_logo_size = 120
                logo_img.thumbnail((max_logo_size, max_logo_size), Image.ANTIALIAS)
                # Make logo circular with white border
                mask = Image.new("L", logo_img.size, 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse((0, 0) + logo_img.size, fill=255)
                logo_img.putalpha(mask)
                border_size = 6
                border = Image.new("RGBA", (logo_img.size[0] + border_size*2, logo_img.size[1] + border_size*2), (255,255,255,255))
                border.paste(logo_img, (border_size, border_size), logo_img)
                logo_img = border
            except Exception as e:
                print(f"Failed to load gym logo: {e}")
        
        # Paste logo at center
        if logo_img:
            logo_w, logo_h = logo_img.size
            pos = ((img_w - logo_w) // 2, (img_h - logo_h) // 2)
            img.paste(logo_img, pos, mask=logo_img)
        
        # Convert to bytes
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=f'qr_code_machine_{machine_id}.png')
        
    except Exception as e:
        return jsonify({'message': f'Failed to generate QR image: {str(e)}'}), 500

@qr_bp.route('/qr/scan', methods=['POST'])
@token_required('client')
def scan_qr_code(current_user):
    try:
        cipher_suite = get_cipher_suite()  # Added to define cipher_suite
        data = request.get_json()
        
        if not data or not data.get('token'):
            return jsonify({'message': 'Token is required'}), 400
        
        token = data['token']
        print(f"Scan QR code token received: {token}")  # Added logging
        
        # Find QR code by token
        qr_code_record = QRCode.query.filter_by(token=token).first()
        
        if not qr_code_record:
            print(f"Invalid QR code token: {token}")  # Added logging
            return jsonify({'message': 'Invalid QR code'}), 404
        
        # Decrypt and verify data
        try:
            encrypted_data = base64.b64decode(qr_code_record.qr_code_data.encode())
            decrypted_data = cipher_suite.decrypt(encrypted_data)
            qr_data = json.loads(decrypted_data.decode())
            
            if qr_data.get('platform') != 'fitcode':
                print(f"QR code platform mismatch: {qr_data.get('platform')}")  # Added logging
                return jsonify({'message': 'QR code not compatible with this platform'}), 400
                
        except Exception as ex:
            import traceback
            print(f"QR code decryption error for token {token}: {ex}")
            traceback.print_exc()
            return jsonify({'message': 'Invalid QR code data'}), 400
        
        # Get machine and gym information
        machine = GymMachine.query.get(qr_code_record.machine_id)
        if not machine:
            print(f"Machine not found for QR code token: {token}")  # Added logging
            return jsonify({'message': 'Machine not found'}), 404
        
        gym = Gym.query.get(machine.gym_id)
        if not gym:
            print(f"Gym not found for machine id {machine.id}")  # Added logging
            return jsonify({'message': 'Gym not found'}), 404
        
        # Record scan history
        scan_record = ScanHistory(
            client_id=current_user.id,
            machine_id=machine.id
        )
        db.session.add(scan_record)
        db.session.commit()
        
        # Get multilingual content
        from src.models.gym import MultilingualContent
        multilingual_content = MultilingualContent.query.filter_by(machine_id=machine.id).all()
        
        return jsonify({
            'message': 'QR code scanned successfully',
            'machine': machine.to_dict(),
            'gym': gym.to_dict(),
            'multilingual_content': [content.to_dict() for content in multilingual_content]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Failed to scan QR code: {e}")  # Added logging
        return jsonify({'message': f'Failed to scan QR code: {str(e)}'}), 500

@qr_bp.route('/qr/validate/<token>', methods=['GET'])
def validate_qr_token(token):
    """Public endpoint to validate if a token is from our platform"""
    try:
        qr_code_record = QRCode.query.filter_by(token=token).first()
        
        if not qr_code_record:
            return jsonify({'valid': False, 'message': 'Invalid token'}), 404
        
        # Decrypt and verify data
        try:
            encrypted_data = base64.b64decode(qr_code_record.qr_code_data.encode())
            decrypted_data = cipher_suite.decrypt(encrypted_data)
            qr_data = json.loads(decrypted_data.decode())
            
            if qr_data.get('platform') != 'fitcode':
                return jsonify({'valid': False, 'message': 'Not a Fitcode QR code'}), 400
                
            return jsonify({'valid': True, 'platform': 'fitcode'}), 200
                
        except Exception:
            return jsonify({'valid': False, 'message': 'Invalid QR code data'}), 400
        
    except Exception as e:
        return jsonify({'valid': False, 'message': f'Validation failed: {str(e)}'}), 500

