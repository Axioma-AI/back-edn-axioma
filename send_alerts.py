import logging
import firebase_admin
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime, time
from firebase_admin import credentials, messaging
from src.config.db_config import engine
from src.models.news_tag_model import NewsModel
from src.utils.logger import setup_logger

logger = setup_logger(__name__, level=logging.DEBUG)

cred = credentials.Certificate("axioma.json")
firebase_app = firebase_admin.initialize_app(cred)
logger.info("Firebase inicializado correctamente.")

SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()


def get_top_news_for_category(session, category, target_date=None):
    """
    Obtiene la noticia con el mayor sentiment_score para una categoría específica,
    desde el inicio del día hasta la hora actual basada en target_date.
    """
    if target_date is None:
        target_date = date.today()

    start_datetime = datetime.combine(target_date, time(0, 0, 0))
    now_time = datetime.now().time()
    end_datetime = datetime.combine(
        target_date, now_time
    )

    logger.info(
        f"Buscando noticias para la categoría {category} entre {start_datetime} y {end_datetime}."
    )

    news = (
        session.query(NewsModel)
        .filter(
            NewsModel.sentiment_category == category,
            NewsModel.publish_datetime.between(start_datetime, end_datetime),
        )
        .order_by(NewsModel.sentiment_score.desc())
        .first()
    )

    if news:
        logger.info(f"✅ Noticia encontrada: ID: {news.id}, Título: {news.title}")
    else:
        logger.info(
            f"⚠️ No se encontraron noticias para la categoría {category} en el rango de {start_datetime} a {end_datetime}."
        )

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

        data_payload = {"id": str(news.id), "title": news.title}

        notification_fields = {"title": news.title}

        detail_present = bool(news.detail)
        image_present = bool(news.image_url)

        if detail_present:
            notification_fields["body"] = news.detail[:200]
            data_payload["detail"] = news.detail

        if image_present:
            notification_fields["image"] = news.image_url
            data_payload["image_url"] = news.image_url

        logger.info(
            f"📦 Campos presentes: Título: ✅ | Detail: {'✅' if detail_present else '❌'} | Image URL: {'✅' if image_present else '❌'}"
        )

        message = messaging.Message(
            notification=messaging.Notification(**notification_fields),
            data=data_payload,
            topic="news",
        )

        response = messaging.send(message)
        logger.info(f"✅ Notificación enviada con éxito. ID: {response}")

    except Exception as e:
        logger.error(f"❌ Error al enviar la notificación: {e}")


def main(prueba_fecha=None):
    """
    Revisa las noticias y envía notificaciones para las categorías MUY_POSITIVO y MUY_NEGATIVO.
    """
    try:
        if prueba_fecha is None:
            prueba_fecha = date.today()
        elif not isinstance(prueba_fecha, date):
            raise ValueError(
                f"El valor de prueba_fecha no es una fecha válida: {prueba_fecha}"
            )

        logger.info(f"Usando la fecha objetivo: {prueba_fecha}")

        positive_news = get_top_news_for_category(session, "MUY_POSITIVO", prueba_fecha)
        if positive_news:
            logger.info(
                f"Enviando notificación para noticia positiva: ID: {positive_news.id}, Título: {positive_news.title}"
            )
            send_notification(positive_news)
        else:
            logger.info(
                "⚠️ No hay noticias positivas para enviar notificaciones en la fecha especificada."
            )

        negative_news = get_top_news_for_category(session, "MUY_NEGATIVO", prueba_fecha)
        if negative_news:
            logger.info(
                f"Enviando notificación para noticia negativa: ID: {negative_news.id}, Título: {negative_news.title}"
            )
            send_notification(negative_news)
        else:
            logger.info(
                "⚠️ No hay noticias negativas para enviar notificaciones en la fecha especificada."
            )

    except Exception as e:
        logger.error(f"❌ Error en el proceso de notificaciones: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    # Puedes pasar una fecha específica descomentando la línea siguiente:
    # main(date(2024, 12, 22))
    main()  # Usa la fecha actual si no se pasa un argumento
