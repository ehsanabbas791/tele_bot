from telegram.ext import ApplicationBuilder,CommandHandler,MessageHandler,filters,ContextTypes
from telegram import Update 
from rembg import remove
from PIL import Image
import os
TOKEN = "8481155252:AAEkFFC47UTGdgzJ3SaH3DRBbyU5pWkOYgI"

#functions in each handler
async def help (update , context):
    await context.bot.send_message(chat_id = update.effective_chat.id,text ="أهلاً وسهلاً بك في خدمة إزالة الخلفية من الصورة ، رجاءً قم بكتابة /start من أجل بدء العملية" )
async def start (update , context):
    await context.bot.send_message(chat_id = update.effective_chat.id,text ="لإزالة الصورة من الخلفية رجاءً أرسل لي الصورة وانتظر بضع ثوان لأرسل لك الصورة بعد التعديل" )
async def handle_message(update:Update , context):
    if filters.PHOTO.check_update(update):
        file_id = update.message.photo[-1].file_id
        unique_file_id = update.message.photo[-1].file_unique_id
        photo_name = f"{unique_file_id}.jpg"

    elif filters.Document.IMAGE:
        file_id = update.message.document.file_id
        _,f_ext = os.path.splitext(update.message.document.file_name)
        unique_file_id = update.message.document.file_unique_id
        photo_name = f"{unique_file_id}{f_ext}"  

    photo_file =  await context.bot.get_file(file_id) 
    await photo_file.download_to_drive(custom_path =f"./temp/{photo_name}")
    await context.bot.send_message(chat_id = update.effective_chat.id, text="تكة...عم نعالج الصورة")


    processed_image = await process_image(photo_name)
    await context.bot.send_document(chat_id=update.effective_chat.id ,document = processed_image)
    os.remove(processed_image)

async def process_image(photo_name: str):
    name, _ = os.path.splitext(photo_name)
    output_photo_path = f"./temp/{name}_white.png"

    # افتح الصورة الأصلية
    input_image = Image.open(f"./temp/{photo_name}")

    # إزالة الخلفية (الناتج يكون بخلفية شفافة)
    removed_bg = remove(input_image).convert("RGBA")

    # إنشاء خلفية بيضاء بنفس حجم الصورة
    white_bg = Image.new("RGBA", removed_bg.size, (255, 255, 255, 255))

    # دمج الصورة مع الخلفية البيضاء
    final_image = Image.alpha_composite(white_bg, removed_bg).convert("RGB")

    # حفظ الصورة النهائية
    final_image.save(output_photo_path, "PNG")

    # حذف الصورة الأصلية
    os.remove(f"./temp/{photo_name}")

    return output_photo_path

if __name__ =='__main__':
    
    application = ApplicationBuilder().token(TOKEN).build()

    #define handlers
    help_handler = CommandHandler('help',help) 
    start_handler = CommandHandler('start',start) 
    message_handler = MessageHandler(filters.PHOTO | filters.Document.IMAGE ,handle_message)


    #register handlers
    application.add_handler(help_handler)
    application.add_handler(start_handler)
    application.add_handler(message_handler)

    


    application.run_polling()