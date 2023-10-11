from flask import Flask
from main import *
app = Flask(__name__)
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor()

future = ''


@app.route('/')
def index():
    return "Hello, World!"


@app.route('/restart/<token>')
def restart_bots(token):
    global future

    if token == API_TOKEN:
        try:
            if future:
                future.cancel()
                logger.info(f'future.cancel() вызван')
                time.sleep(10)
                logger.info(f'таймер завершился')
            future = executor.submit(main)
            return {'result': True, 'message': 'BOT WAS RESTARTED'}
        except Exception:
            logger.exception(Exception)
            return {'result': False, 'message': Exception}
    else:
        return {'result': False, 'message': 'ACCESS DENIED'}


# with app.app_context():
#     main()
    # future = executor.submit(main)


if __name__ == '__main__':
    app.run(debug=True)