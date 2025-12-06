"""Fix chris.trunell@gmail.com login issue"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import bcrypt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def fix_user():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Clear reset token
    result = await db.users.update_one(
        {'email': 'chris.trunell@gmail.com'},
        {
            '$unset': {
                'reset_token': '',
                'reset_token_expires': ''
            }
        }
    )
    
    if result.modified_count > 0:
        print('✅ Cleared reset token from chris.trunell@gmail.com')
    else:
        print('⚠️  No reset token to clear (or user not found)')
    
    # Set a known password for testing: TestPass123!
    password = 'TestPass123!'
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    result2 = await db.users.update_one(
        {'email': 'chris.trunell@gmail.com'},
        {'$set': {'password_hash': hashed.decode('utf-8')}}
    )
    
    if result2.modified_count > 0:
        print(f'✅ Set new password')
        print('\n' + '='*50)
        print('You can now login with:')
        print('='*50)
        print('Email: chris.trunell@gmail.com')
        print(f'Password: {password}')
        print('='*50)
    else:
        print('❌ Failed to update password')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_user())
