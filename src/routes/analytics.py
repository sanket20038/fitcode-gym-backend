from flask import Blueprint, request, jsonify
from src.models.gym import db, ScanHistory, GymMachine, Gym
from src.routes.auth import token_required
from sqlalchemy import func, desc
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics/overview', methods=['GET'])
@token_required('owner')
def get_analytics_overview(current_user):
    try:
        gym = Gym.query.filter_by(owner_id=current_user.id).first()
        
        if not gym:
            return jsonify({'message': 'No gym found for this owner'}), 404
        
        # Get date range from query params
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total machines
        total_machines = GymMachine.query.filter_by(gym_id=gym.id).count()
        
        # Total scans
        total_scans = db.session.query(ScanHistory).join(
            GymMachine, ScanHistory.machine_id == GymMachine.id
        ).filter(
            GymMachine.gym_id == gym.id
        ).count()
        
        # Scans in date range
        recent_scans = db.session.query(ScanHistory).join(
            GymMachine, ScanHistory.machine_id == GymMachine.id
        ).filter(
            GymMachine.gym_id == gym.id,
            ScanHistory.scan_timestamp >= start_date
        ).count()
        
        # Unique users in date range
        unique_users = db.session.query(func.count(func.distinct(ScanHistory.client_id))).join(
            GymMachine, ScanHistory.machine_id == GymMachine.id
        ).filter(
            GymMachine.gym_id == gym.id,
            ScanHistory.scan_timestamp >= start_date
        ).scalar()
        
        return jsonify({
            'overview': {
                'total_machines': total_machines,
                'total_scans': total_scans,
                'recent_scans': recent_scans,
                'unique_users': unique_users or 0,
                'date_range_days': days
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to retrieve analytics overview: {str(e)}'}), 500

@analytics_bp.route('/analytics/machine-usage', methods=['GET'])
@token_required('owner')
def get_machine_usage(current_user):
    try:
        gym = Gym.query.filter_by(owner_id=current_user.id).first()
        
        if not gym:
            return jsonify({'message': 'No gym found for this owner'}), 404
        
        # Get date range from query params
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Machine usage statistics
        machine_usage = db.session.query(
            GymMachine.id,
            GymMachine.name,
            func.count(ScanHistory.id).label('scan_count')
        ).outerjoin(
            ScanHistory, GymMachine.id == ScanHistory.machine_id
        ).filter(
            GymMachine.gym_id == gym.id
        ).filter(
            db.or_(
                ScanHistory.scan_timestamp >= start_date,
                ScanHistory.scan_timestamp.is_(None)
            )
        ).group_by(
            GymMachine.id, GymMachine.name
        ).order_by(desc('scan_count')).all()
        
        usage_data = []
        for machine_id, machine_name, scan_count in machine_usage:
            usage_data.append({
                'machine_id': machine_id,
                'machine_name': machine_name,
                'scan_count': scan_count or 0
            })
        
        return jsonify({
            'machine_usage': usage_data,
            'date_range_days': days
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to retrieve machine usage: {str(e)}'}), 500

@analytics_bp.route('/analytics/daily-scans', methods=['GET'])
@token_required('owner')
def get_daily_scans(current_user):
    try:
        gym = Gym.query.filter_by(owner_id=current_user.id).first()
        
        if not gym:
            return jsonify({'message': 'No gym found for this owner'}), 404
        
        # Get date range from query params
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily scan counts
        daily_scans = db.session.query(
            func.date(ScanHistory.scan_timestamp).label('scan_date'),
            func.count(ScanHistory.id).label('scan_count')
        ).join(
            GymMachine, ScanHistory.machine_id == GymMachine.id
        ).filter(
            GymMachine.gym_id == gym.id,
            ScanHistory.scan_timestamp >= start_date
        ).group_by(
            func.date(ScanHistory.scan_timestamp)
        ).order_by('scan_date').all()
        
        daily_data = []
        for scan_date, scan_count in daily_scans:
            daily_data.append({
                'date': scan_date.isoformat() if scan_date else None,
                'scan_count': scan_count
            })
        
        return jsonify({
            'daily_scans': daily_data,
            'date_range_days': days
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to retrieve daily scans: {str(e)}'}), 500

@analytics_bp.route('/analytics/popular-machines', methods=['GET'])
@token_required('owner')
def get_popular_machines(current_user):
    try:
        gym = Gym.query.filter_by(owner_id=current_user.id).first()
        
        if not gym:
            return jsonify({'message': 'No gym found for this owner'}), 404
        
        limit = request.args.get('limit', 5, type=int)
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Most popular machines
        popular_machines = db.session.query(
            GymMachine.id,
            GymMachine.name,
            func.count(ScanHistory.id).label('scan_count'),
            func.count(func.distinct(ScanHistory.client_id)).label('unique_users')
        ).join(
            ScanHistory, GymMachine.id == ScanHistory.machine_id
        ).filter(
            GymMachine.gym_id == gym.id,
            ScanHistory.scan_timestamp >= start_date
        ).group_by(
            GymMachine.id, GymMachine.name
        ).order_by(desc('scan_count')).limit(limit).all()
        
        popular_data = []
        for machine_id, machine_name, scan_count, unique_users in popular_machines:
            popular_data.append({
                'machine_id': machine_id,
                'machine_name': machine_name,
                'scan_count': scan_count,
                'unique_users': unique_users
            })
        
        return jsonify({
            'popular_machines': popular_data,
            'date_range_days': days,
            'limit': limit
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to retrieve popular machines: {str(e)}'}), 500

