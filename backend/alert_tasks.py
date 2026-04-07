"""
Scheduled task functions for NoFeesApts.
These are used by both the scheduler and admin trigger endpoints.
"""
from datetime import datetime, timezone, timedelta
import logging

from database import db
from services import SMS_SERVICE_AVAILABLE, sms_functions

logger = logging.getLogger(__name__)


async def process_saved_search_alerts():
    """Process saved search alerts and send email notifications"""
    from smtp_email_service import send_saved_search_alert_email

    logger.info("Processing saved search alerts...")

    try:
        searches = await db.saved_searches.find({
            'is_active': True
        }).to_list(1000)

        alerts_sent = 0

        for search in searches:
            try:
                query = {'is_available': True}

                if search.get('bedrooms') is not None:
                    query['bedrooms'] = search['bedrooms']
                if search.get('min_rent'):
                    query['rent'] = query.get('rent', {})
                    query['rent']['$gte'] = search['min_rent']
                if search.get('max_rent'):
                    query['rent'] = query.get('rent', {})
                    query['rent']['$lte'] = search['max_rent']
                if search.get('bathrooms'):
                    query['bathrooms'] = search['bathrooms']

                last_checked = search.get('last_checked_at')
                if last_checked:
                    if isinstance(last_checked, str):
                        last_checked_dt = datetime.fromisoformat(last_checked)
                    else:
                        last_checked_dt = last_checked
                    query['created_at'] = {'$gt': last_checked_dt.isoformat()}
                else:
                    yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
                    query['created_at'] = {'$gt': yesterday.isoformat()}

                notified_ids = search.get('notified_unit_ids', [])
                if notified_ids:
                    query['id'] = {'$nin': notified_ids}

                units = await db.units.find(query, {"_id": 0}).limit(20).to_list(20)

                if search.get('state') or search.get('neighborhood'):
                    building_query = {}
                    if search.get('state'):
                        building_query['state'] = search['state']
                    if search.get('neighborhood'):
                        building_query['neighborhood'] = {'$regex': search['neighborhood'], '$options': 'i'}

                    if building_query:
                        buildings = await db.buildings.find(building_query, {"_id": 0}).to_list(1000)
                        building_ids = {b['id'] for b in buildings}
                        units = [u for u in units if u.get('building_id') in building_ids]

                if units:
                    for unit in units:
                        building = await db.buildings.find_one(
                            {'id': unit.get('building_id')},
                            {"_id": 0}
                        )
                        unit['building'] = building

                    user = await db.users.find_one({'id': search['user_id']})
                    user_name = user.get('name', 'Apartment Hunter') if user else 'Apartment Hunter'

                    search_criteria = {
                        'bedrooms': search.get('bedrooms'),
                        'min_rent': search.get('min_rent'),
                        'max_rent': search.get('max_rent'),
                        'state': search.get('state'),
                        'neighborhood': search.get('neighborhood')
                    }

                    notification_sent = False

                    if search.get('notify_email', True):
                        email_sent = send_saved_search_alert_email(
                            user_email=search['user_email'],
                            user_name=user_name,
                            search_name=search['name'],
                            matching_units=units,
                            search_criteria=search_criteria
                        )
                        if email_sent:
                            notification_sent = True
                            logger.info(f"Email alert sent to {search['user_email']} for search '{search['name']}'")

                    if search.get('notify_sms') and search.get('user_phone') and SMS_SERVICE_AVAILABLE:
                        send_saved_search_alert_sms = sms_functions.get('send_saved_search_alert_sms')
                        if send_saved_search_alert_sms:
                            sms_sent = send_saved_search_alert_sms(
                                phone_number=search['user_phone'],
                                search_name=search['name'],
                                matching_units=units
                            )
                            if sms_sent:
                                notification_sent = True
                                logger.info(f"SMS alert sent to {search['user_phone']} for search '{search['name']}'")

                    if notification_sent:
                        alerts_sent += 1
                        new_notified_ids = notified_ids + [u['id'] for u in units]
                        await db.saved_searches.update_one(
                            {'id': search['id']},
                            {
                                '$set': {
                                    'last_checked_at': datetime.now(timezone.utc).isoformat(),
                                    'last_alert_sent': datetime.now(timezone.utc).isoformat(),
                                    'notified_unit_ids': new_notified_ids[-100:]
                                }
                            }
                        )
                        logger.info(f"Alerts sent for search '{search['name']}' with {len(units)} units")
                else:
                    await db.saved_searches.update_one(
                        {'id': search['id']},
                        {'$set': {'last_checked_at': datetime.now(timezone.utc).isoformat()}}
                    )

            except Exception as e:
                logger.error(f"Error processing search {search.get('id')}: {e}")
                continue

        logger.info(f"Saved search alerts completed: {alerts_sent} alerts sent")
        return alerts_sent

    except Exception as e:
        logger.error(f"Error in saved search alerts job: {e}")
        return 0
