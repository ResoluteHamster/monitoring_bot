

<br>
<p style="margin-left: 40px;">Приветствую!</p>


<p style="margin-left: 40px;">Приложение определяет собственное движение фьючерса ETHUSDT<br>
	исключая влияние BTCUSDT с помощью корреляции Пирсона.<br>
	Мне показалось, такое решение позволяет выполнить задачу и не является сложным.</p>

<p style="margin-left: 40px;">Для запуска проекта необходим Docker.<br>
	Зайдите в папку проекта из терминала, далее соберите образ:<br>
	<br>
	docker build -t monitoring_image .    <br>
	Затем запускайте:<br>
	docker run -d --name monitoring_bot monitoring_image<br>
	Для просмотра сообщений:<br>
	docker logs monitoring_bot --follow</p>


