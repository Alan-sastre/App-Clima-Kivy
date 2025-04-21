from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.network.urlrequest import UrlRequest
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, Line
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget

import json
from datetime import datetime, timedelta
import urllib.parse

# Custom divider widget


class Divider(Widget):
    def __init__(self, **kwargs):
        super(Divider, self).__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(1)
        with self.canvas:
            Color(0.8, 0.8, 0.8, 1)  # Light gray color
            self.line = Rectangle(pos=self.pos, size=(self.width, dp(1)))

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, instance, value):
        self.line.pos = self.pos
        self.line.size = (self.width, dp(1))


class WeatherApp(App):
    API_KEY = "7398b838552585f5cd13fe3409c757a1"

    def build(self):
        # Set window properties
        self.title = "Clima Actual con Análisis de Lluvia"
        Window.size = (500, 700)

        # Main layout
        self.main_layout = BoxLayout(
            orientation='vertical', padding=dp(20), spacing=dp(20))
        self.main_layout.bind(size=self._update_rect, pos=self._update_rect)

        with self.main_layout.canvas.before:
            Color(0.93, 0.93, 0.93, 1)  # Light gray background (GREY_200)
            self.rect = Rectangle(
                size=self.main_layout.size, pos=self.main_layout.pos)

        # Title
        title_label = Label(
            text="Clima Actual con Análisis de Lluvia",
            font_size=dp(24),
            color=(0.11, 0.40, 0.53, 1),  # BLUE_800
            size_hint_y=None,
            height=dp(50)
        )

        # Input section
        self.city_input = TextInput(
            hint_text="Ingresa una ciudad",
            multiline=False,
            size_hint_y=None,
            height=dp(50),
            font_size=dp(16),
            padding=[dp(10), dp(10), dp(10), dp(10)]
        )

        # Search button
        search_button = Button(
            text="Buscar Clima",
            size_hint=(None, None),
            size=(dp(200), dp(50)),
            pos_hint={'center_x': 0.5},
            background_color=(0.22, 0.47, 0.69, 1),  # BLUE_700
            color=(1, 1, 1, 1)  # WHITE
        )
        search_button.bind(on_release=self.get_weather)

        # Loading indicator
        self.loading_indicator = Label(
            text="Cargando...",
            color=(0.22, 0.47, 0.69, 1),  # BLUE_700
            opacity=0
        )

        # Result container
        result_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(350),
            padding=dp(15)
        )
        with result_container.canvas.before:
            Color(1, 1, 1, 1)  # WHITE
            Rectangle(pos=result_container.pos, size=result_container.size)
        result_container.bind(pos=self._update_result_rect,
                              size=self._update_result_rect)

        # ScrollView for results
        scroll_view = ScrollView(size_hint=(1, 1))
        self.result_layout = BoxLayout(
            orientation='vertical', spacing=dp(90), size_hint_y=None)
        self.result_layout.bind(
            minimum_height=self.result_layout.setter('height'))
        scroll_view.add_widget(self.result_layout)
        result_container.add_widget(scroll_view)

        # Add all widgets to main layout
        self.main_layout.add_widget(title_label)
        self.main_layout.add_widget(self.city_input)
        self.main_layout.add_widget(search_button)
        self.main_layout.add_widget(self.loading_indicator)
        self.main_layout.add_widget(result_container)

        return self.main_layout

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _update_result_rect(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(1, 1, 1, 1)  # WHITE
            Rectangle(pos=instance.pos, size=instance.size)

    def get_weather(self, instance):
        ciudad = self.city_input.text.strip()
        if not ciudad:
            self.show_error("Por favor, ingresa una ciudad")
            return

        # Show loading indicator
        self.loading_indicator.opacity = 1

        # Make request for current weather
        url_actual = f"http://api.openweathermap.org/data/2.5/weather?q={urllib.parse.quote(ciudad)}&units=metric&lang=es&appid={self.API_KEY}"

        # In Kivy we use UrlRequest instead of requests
        req_actual = UrlRequest(
            url_actual,
            on_success=self.got_current_weather,
            on_error=self.on_request_error,
            on_failure=self.on_request_error
        )

    def got_current_weather(self, req, data_actual):
        if data_actual.get('cod') != 200:
            self.show_error(
                f"Error: {data_actual.get('message', 'Ciudad no encontrada')}")
            self.loading_indicator.opacity = 0
            return

        # Store current weather data
        self.data_actual = data_actual

        # Get forecast for rain analysis
        ciudad = self.city_input.text.strip()
        url_pronostico = f"http://api.openweathermap.org/data/2.5/forecast?q={urllib.parse.quote(ciudad)}&units=metric&lang=es&appid={self.API_KEY}"

        req_pronostico = UrlRequest(
            url_pronostico,
            on_success=self.process_weather_data,
            on_error=self.on_request_error,
            on_failure=self.on_request_error
        )

    def on_request_error(self, req, error):
        self.show_error(f"Error de conexión: {error}")
        self.loading_indicator.opacity = 0

    def process_weather_data(self, req, data_pronostico):
        self.loading_indicator.opacity = 0

        if data_pronostico.get('cod') != '200':
            self.show_error(
                f"Error al obtener pronóstico: {data_pronostico.get('message', '')}")
            return

        # Extract current data
        data_actual = self.data_actual
        temp_actual = data_actual["main"]["temp"]
        sensacion = data_actual["main"]["feels_like"]
        humedad = data_actual["main"]["humidity"]
        nombre_ciudad = data_actual["name"] + \
            ", " + data_actual["sys"]["country"]
        fecha_actualizacion = datetime.fromtimestamp(
            data_actual["dt"]).strftime('%d/%m/%Y %H:%M')
        icono = data_actual["weather"][0]["icon"]
        icono_url = f"http://openweathermap.org/img/wn/{icono}@2x.png"
        descripcion = data_actual["weather"][0]["description"].capitalize()

        # Analyze rain frequency
        analisis_lluvia = self.analizar_frecuencia_lluvia(
            data_pronostico["list"])

        # Clear previous results
        self.result_layout.clear_widgets()

        # City name and icon
        city_row = BoxLayout(size_hint_y=None, height=dp(60))
        city_label = Label(
            text=nombre_ciudad,
            font_size=dp(22),
            color=(0.11, 0.40, 0.53, 1),  # BLUE_900
            bold=True,
            size_hint=(0.7, 1)
        )
        weather_icon = AsyncImage(
            source=icono_url,
            size_hint=(0.3, 1)
        )
        city_row.add_widget(city_label)
        city_row.add_widget(weather_icon)
        self.result_layout.add_widget(city_row)

        # Divider
        self.result_layout.add_widget(Divider())

        # Temperature
        self.result_layout.add_widget(
            Label(
                text=f"🌡 {temp_actual:.1f}°C (Sensación: {sensacion:.1f}°C)",
                font_size=dp(18),
                color=(0.11, 0.40, 0.53, 1),  # BLUE_900
                bold=True,
                size_hint_y=None,
                height=dp(30),
                halign='left',
                valign='middle',
                text_size=(Window.width-dp(60), dp(30))
            )
        )

        # Humidity
        self.result_layout.add_widget(
            Label(
                text=f"💧 Humedad: {humedad}%",
                font_size=dp(16),
                color=(0.16, 0.40, 0.65, 1),  # BLUE_800
                size_hint_y=None,
                height=dp(30),
                halign='left',
                valign='middle',
                text_size=(Window.width-dp(60), dp(30))
            )
        )

        # Description
        self.result_layout.add_widget(
            Label(
                text=f"📌 {descripcion}",
                font_size=dp(16),
                color=(0.16, 0.40, 0.65, 1),  # BLUE_800
                size_hint_y=None,
                height=dp(30),
                halign='left',
                valign='middle',
                text_size=(Window.width-dp(60), dp(30))
            )
        )

        # Update time
        self.result_layout.add_widget(
            Label(
                text=f"🕒 Actualizado: {fecha_actualizacion}",
                font_size=dp(12),
                color=(0.5, 0.57, 0.65, 1),  # BLUE_GREY_500
                size_hint_y=None,
                height=dp(20),
                halign='left',
                valign='middle',
                text_size=(Window.width-dp(60), dp(20))
            )
        )

        # Divider
        self.result_layout.add_widget(Divider())

        # Rain analysis title
        self.result_layout.add_widget(
            Label(
                text="Análisis de Lluvia para los próximos días:",
                font_size=dp(16),
                color=(0.11, 0.40, 0.53, 1),  # BLUE_900
                bold=True,
                size_hint_y=None,
                height=dp(30),
                halign='left',
                valign='middle',
                text_size=(Window.width-dp(60), dp(30))
            )
        )

        # Rain analysis content
        self.result_layout.add_widget(
            Label(
                text=analisis_lluvia,
                font_size=dp(14),
                color=(0.16, 0.40, 0.65, 1),  # BLUE_800
                size_hint_y=None,
                height=dp(80),
                halign='left',
                valign='top',
                text_size=(Window.width-dp(60), dp(80))
            )
        )

    def analizar_frecuencia_lluvia(self, pronostico_lista):
        # Agrupar por día y contar días con lluvia
        dias_analizados = 5
        dias_con_lluvia = 0
        dias_totales = 0
        precipitacion_total = 0

        # Fechas únicas para no contar el mismo día múltiples veces
        fechas_analizadas = set()

        for item in pronostico_lista:
            fecha = datetime.fromtimestamp(item["dt"]).date()
            if fecha in fechas_analizadas:
                continue

            fechas_analizadas.add(fecha)
            if len(fechas_analizadas) > dias_analizados:
                break

            if "rain" in item:
                dias_con_lluvia += 1
                precipitacion_total += item["rain"].get("3h", 0)
            dias_totales += 1

        if dias_totales == 0:
            return "No hay datos suficientes para el análisis de lluvia."

        porcentaje_lluvia = (dias_con_lluvia / dias_totales) * 100
        precipitacion_promedio = precipitacion_total / \
            dias_con_lluvia if dias_con_lluvia > 0 else 0

        if porcentaje_lluvia == 0:
            return "No se esperan lluvias en los próximos días. ☀️"
        elif porcentaje_lluvia < 30:
            return f"Baja probabilidad de lluvia ({porcentaje_lluvia:.0f}% de los días). Algunas precipitaciones ligeras posibles. 🌦️"
        elif porcentaje_lluvia < 60:
            return f"Moderada probabilidad de lluvia ({porcentaje_lluvia:.0f}% de los días). Precipitación promedio: {precipitacion_promedio:.1f}mm. 🌧️"
        else:
            return f"Alta probabilidad de lluvia ({porcentaje_lluvia:.0f}% de los días). Precipitación significativa esperada ({precipitacion_promedio:.1f}mm promedio). ⛈️"

    def show_error(self, mensaje):
        self.result_layout.clear_widgets()
        self.result_layout.add_widget(
            Label(
                text=mensaje,
                font_size=dp(16),
                color=(1, 0, 0, 1),  # RED
                size_hint_y=None,
                height=dp(50)
            )
        )


if __name__ == '__main__':
    WeatherApp().run()
