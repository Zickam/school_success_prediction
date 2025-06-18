import os
import sys
import asyncio

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.join(SCRIPT_DIR, "../", "logging_setup.py")))

import logging_setup
logging_setup.init("logs/tg_bot.log")
import logging


# async def addExpirationNotificationsToExistingUsers():
#     from tg_bot.user.routers.keys import getFSMContext
#     from tg_bot.user.routers.keys import addConfigExpirationNotification
#     from app import models
#
#     for config in await models.Config.all():
#         if await config.isActive():
#             fsm = await getFSMContext(config.user_id)
#             await addConfigExpirationNotification(config, config.user_id, fsm)
#             logging.info(f"added expiration notification trigger for {config.user_id}")


async def main():
    from tg_bot.config import dp, bot
    from tg_bot.filters import IsPrivate, IsPrivateCallback
    from tg_bot.routers.user.init_routers import router as user_router
    # await bot.delete_webhook(drop_pending_updates=True)

    dp.message.filter(IsPrivate())
    dp.callback_query.filter(IsPrivateCallback())


    dp.include_routers(
        user_router,
        # user_routers.router,
    )

    await dp.start_polling(bot)

    logging.info("Bot polling started")


if __name__ == "__main__":
    asyncio.run(main())
