from flask import Blueprint, request, jsonify
from py_zipkin.zipkin import zipkin_span, ZipkinAttrs, Encoding
from app.services.prediction_service import predict_count_service
from app.utils.zipkin_transport import zipkin_transport_handler

prediction_blueprint = Blueprint('prediction', __name__)

@prediction_blueprint.route('/predict-count', methods=['GET'])
def predict_count():
    zipkin_attrs = ZipkinAttrs(
        trace_id=request.headers.get('X-B3-TraceID'),
        span_id=request.headers.get('X-B3-SpanID'),
        parent_span_id=request.headers.get('X-B3-ParentSpanID'),
        flags=request.headers.get('X-B3-Flags'),
        is_sampled=request.headers.get('X-B3-Sampled'),
    )

    with zipkin_span(
            service_name="predict_count_by_time",
            zipkin_attrs=zipkin_attrs,
            span_name="predict_count_by_time",
            transport_handler=zipkin_transport_handler,
            port=5000,
            sample_rate=100,
            encoding=Encoding.V2_JSON
    ):
        log_level = request.args.get('log_level', 'WARN')
        steps = int(request.args.get('steps', 1))
        return predict_count_service(log_level, steps)


