"""
Audit routes for checking entry naming conventions.
"""

from flask import Blueprint, request, jsonify, g
from backend.routes.entries import supabase_auth_required
from backend.services.entry_audit import audit_entries, fix_legacy_entry_title_date
from backend.config.logging import get_logger

logger = get_logger(__name__)

audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit')


@audit_bp.route('/entries', methods=['GET'])
@supabase_auth_required
def audit_user_entries():
    """
    Audit all entries for the current user to check naming convention compliance.
    Returns statistics and list of entries that don't follow the convention.
    """
    try:
        result = audit_entries(g.user_supabase, user_id=g.current_user.id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.exception("Error auditing entries", extra={
            "route": "/api/audit/entries",
            "method": "GET",
            "user_id": g.current_user.id
        })
        return jsonify({'error': 'Internal server error'}), 500


@audit_bp.route('/entries/fix-legacy', methods=['POST'])
@supabase_auth_required
def fix_legacy_entries():
    """
    Fix legacy entries (without time component) by adding time to title_date.
    Can fix a specific entry or all legacy entries.
    """
    try:
        data = request.get_json() or {}
        
        # Get legacy entries
        audit_result = audit_entries(g.user_supabase, user_id=g.current_user.id)
        legacy_entries = [issue for issue in audit_result['issues'] if 'legacy' in issue.get('issue', '').lower()]
        
        if not legacy_entries:
            return jsonify({
                'message': 'No legacy entries found',
                'fixed_count': 0
            }), 200
        
        # Fix specific entry if provided
        if 'user_and_entry_id' in data:
            target_id = data['user_and_entry_id']
            entry = next((e for e in legacy_entries if e['user_and_entry_id'] == target_id), None)
            if entry:
                success = fix_legacy_entry_title_date(entry, g.user_supabase)
                return jsonify({
                    'message': 'Entry fixed' if success else 'Failed to fix entry',
                    'fixed_count': 1 if success else 0
                }), 200 if success else 500
            else:
                return jsonify({'error': 'Entry not found or not a legacy entry'}), 404
        
        # Fix all legacy entries
        fixed_count = 0
        for entry in legacy_entries:
            if fix_legacy_entry_title_date(entry, g.user_supabase):
                fixed_count += 1
        
        return jsonify({
            'message': f'Fixed {fixed_count} legacy entries',
            'fixed_count': fixed_count,
            'total_legacy': len(legacy_entries)
        }), 200
        
    except Exception as e:
        logger.exception("Error fixing legacy entries", extra={
            "route": "/api/audit/entries/fix-legacy",
            "method": "POST",
            "user_id": g.current_user.id
        })
        return jsonify({'error': 'Internal server error'}), 500

