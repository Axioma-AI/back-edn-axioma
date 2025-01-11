import logging
import firebase_admin
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from datetime import date, datetime, time  # Importamos date explícitamente
from firebase_admin import credentials, messaging
from src.config.db_config import engine
from src.models.news_tag_model import NewsModel
from src.utils.logger import setup_logger

# Configura el logger
logger = setup_logger(__name__, level=logging.DEBUG)

# Inicializa Firebase
cred = credentials.Certificate("axioma.json")  # Ruta al archivo JSON
firebase_app = firebase_admin.initialize_app(cred)
logger.info("Firebase inicializado correctamente.")

# Configuración de la base de datos
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

def get_top_news_for_category(session, category, target_date=None):
    """
    Obtiene la noticia con el mayor sentiment_score para una categoría específica,
    desde el inicio del día hasta la hora actual basada en target_date.
    """
    # Si no se proporciona target_date, usamos la fecha de hoy
    if target_date is None:
        target_date = date.today()

    # Define el inicio del día (00:00:00) y la hora actual pero usando la fecha objetivo
    start_datetime = datetime.combine(target_date, time(0, 0, 0))  # 00:00:00
    now_time = datetime.now().time()  # Hora actual del sistema
    end_datetime = datetime.combine(target_date, now_time)  # Hora actual, pero en target_date

    logger.info(f"Buscando noticias para la categoría {category} entre {start_datetime} y {end_datetime}.")

    # Filtro usando BETWEEN para el rango dinámico de tiempo
    news = (
        session.query(NewsModel)
        .filter(
            NewsModel.sentiment_category == category,
            NewsModel.publish_datetime.between(start_datetime, end_datetime)
        )
        .order_by(NewsModel.sentiment_score.desc())
        .first()
    )

    if news:
        logger.info(f"✅ Noticia encontrada: ID: {news.id}, Título: {news.title}")
    else:
        logger.info(f"⚠️ No se encontraron noticias para la categoría {category} en el rango de {start_datetime} a {end_datetime}.")
    
    return news

def send_notification(news):
    """
    Envía una notificación push usando Firebase para una noticia específica.
    """
    if not news:
        logger.info("No hay noticias relevantes para enviar notificaciones.")
        return

    try:
        logger.info(f"Preparando notificación: ID: {news.id}, Título: {news.title}")

        # Configurar mensaje de Firebase
        message = messaging.Message(
            notification=messaging.Notification(
                title=news.title,
                body=news.detail[:200],
                image=news.image_url,
            ),
            data={
                "id": str(news.id),
                "title": news.title,
                "detail": news.detail,
                "image_url": news.image_url,
            },
            topic="news",
        )

        # Envía el mensaje
        response = messaging.send(message)
        logger.info(f"✅ Notificación enviada con éxito. ID: {response}")

    except Exception as e:
        logger.error(f"❌ Error al enviar la notificación: {e}")

def main(prueba_fecha=None):
    """
    Revisa las noticias y envía notificaciones para las categorías MUY_POSITIVO y MUY_NEGATIVO.
    """
    try:
        # Si no se proporciona una fecha específica, usamos la fecha de hoy
        if prueba_fecha is None:
            prueba_fecha = date.today()
        elif not isinstance(prueba_fecha, date):
            raise ValueError(f"El valor de prueba_fecha no es una fecha válida: {prueba_fecha}")

        logger.info(f"Usando la fecha objetivo: {prueba_fecha}")

        # Obtener noticias más relevantes por categoría MUY_POSITIVO
        positive_news = get_top_news_for_category(session, 'MUY_POSITIVO', prueba_fecha)
        if positive_news:
            logger.info(f"Enviando notificación para noticia positiva: ID: {positive_news.id}, Título: {positive_news.title}")
            send_notification(positive_news)
        else:
            logger.info("⚠️ No hay noticias positivas para enviar notificaciones en la fecha especificada.")

        # Obtener noticias más relevantes por categoría MUY_NEGATIVO
        negative_news = get_top_news_for_category(session, 'MUY_NEGATIVO', prueba_fecha)
        if negative_news:
            logger.info(f"Enviando notificación para noticia negativa: ID: {negative_news.id}, Título: {negative_news.title}")
            send_notification(negative_news)
        else:
            logger.info("⚠️ No hay noticias negativas para enviar notificaciones en la fecha especificada.")

    except Exception as e:
        logger.error(f"❌ Error en el proceso de notificaciones: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    # Puedes pasar una fecha específica descomentando la línea siguiente:
    # main(date(2024, 12, 22))
    main()  # Usa la fecha actual si no se pasa un argumento
    