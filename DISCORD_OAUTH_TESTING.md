# Discord OAuth Household Gate - Manual Testing Guide

## Quick Test (5 minutes)

### Setup
1. Start backend: `source .venv/bin/activate && python main.py`
2. Start frontend: `npm run dev`
3. Have a Discord account ready

### Test Flow
1. Navigate to `http://localhost:5173`
2. Click "Login with Discord"
3. Authorize the app on Discord
4. **Expected result**:
   - New user → Redirects to `/household-setup` (no household yet)
   - Existing user with household → Redirects to home
5. After household setup, try `/set_channel` bot command
6. **Expected result**: Bot responds (household exists)

### Verify Household Created
```bash
# In another terminal:
sqlite3 bro_graph.sqlite "SELECT * FROM households WHERE user_id = (SELECT id FROM users WHERE discord_id = 'YOUR_DISCORD_ID');"
```
Should return a row with household data.

## What Was Fixed

### Backend (routes/auth.py line 89-94)
- When new Discord user is created, household is auto-created
- Prevents "no household" blocker

### Frontend (DiscordCallback.tsx line 34-43)
- After Discord login, check if user has household_id
- If missing: redirect to `/household-setup`
- If exists: redirect to home

## Tests Passing
- Backend: 2/2 tests pass
- Frontend: 5/5 tests pass
- All tests follow Bootstrap ESP (CLARITY 4, ERRORS 4, PRACTICALITY 4)

## If It Breaks
- Check database: Is household created?
- Check frontend console: Does authService.getUser() have household_id?
- Check backend logs: Any errors in discord_callback?

## Next Steps
Manual test on Discord account and ship.
