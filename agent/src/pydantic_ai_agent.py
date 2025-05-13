import os

import psycopg2
from openai import AsyncOpenAI
from pydantic_ai import Agent, Tool
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider


db_params = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}


def sql_engine(query: str) -> str:
    """Allow you to perform SQL queries on the table. Returns a string representation of the result.

    The table is named "resumes". Its description is as follows:

    Table Schema for "resumes?:
    - id (integer)              - primary key
    - contact_info (jsonb)      - {"email": "...", "phone": "...", ...}
    - experience (jsonb)        - list of work-experience blocks
    - education (jsonb)         - list of education blocks
    - portfolio (jsonb)         - list of projects {"name", "link", "description"}
    - languages (ARRAY)         - ['Русский – родной', 'Английский – B2', ...]
    - skills (ARRAY)            - ['Kubernetes', 'Python', ...]
    - certifications (ARRAY)     - certificates
    - hobbies (ARRAY)           - hobbies
    - name (text)               - full name (UTF-8)
    - gender (text)             - «женский», «мужской»,
    - title (text)              - current/target job titles(nullable)
    - summary (text)            - short profile with description  of position
    First 5 rows from `resumes`:
    id | name | gender | title | summary | contact_info | skills | experience | education | languages | certifications | hobbies | portfolio
    1 | Зыкова Валерия Кузьминична | женский | Mobile Developer | Опытный мобильный разработчик с 5-летним стажем в разработке и оптимизации мобильных приложений. Обладаю глубоким пониманием современных технологий и платформ, таких как iOS и Android. Сильные навыки в проектировании, разработке и тестировании приложений, а также в работе в команде и управлении проектами. Ищу возможность применить свои навыки и знания в динамичной и инновационной компании. | {'email': 'valeriya.zykova@example.com', 'phone': '+7 (808) 262-35-84', 'github': 'github.com/valeriya-zykova', 'linkedin': 'linkedin.com/in/valeriya-zykova', 'location': 'Чехия'} | ['Swift', 'Kotlin', 'React Native', 'Firebase', 'Git', 'Agile/Scrum', 'UX/UI Design', 'RESTful APIs', 'CI/CD', 'Test-Driven Development'] | [{'company': 'TechSolutions', 'end_date': '2023-05-31', 'job_title': 'Mobile Developer', 'start_date': '2018-06-01', 'achievements': ['Разработала и запустила 3 мобильных приложения для iOS и Android, которые достигли более 100 000 загрузок.', 'Оптимизировала производительность приложений, сократив время загрузки на 30%.', 'Внедрила CI/CD пайплайны, что сократило время развертывания на 50%.', 'РаЬотала в мультидисциплинарной команде, координируя усилия разработчиков, дизайнеров и тестировщиков.']}] | [{'degree': 'Бакалавр информационных технологий', 'details': 'Специализация: Программная инженерия', 'end_date': '2017-06-30', 'start_date': '2013-09-01', 'institution': 'Санкт-Петербургский Политехнический Университет'}] | ['Русский – родной', 'Английский – B2', 'Чешский – A2'] | ['Google Certified Professional Cloud Developer', 'Apple Developer Program'] | ['Фотография', 'Путешествия', 'Программирование в свободное время'] | [{'link': 'github.com/valeriya-zykova/TravelApp', 'name': 'TravelApp', 'description': 'Мобильное приложение для планирования путешествий. Использовались технологии: Swift, Firebase, MapKit. Приложение позволяет пользователям создавать маршруты, добавлять точки интереса и делиться планами с друзьями.'}, {'link': 'github.com/valeriya-zykova/FitnessTracker', 'name': 'FitnessTracker', 'description': 'Приложение для отслеживания физической активности. Использовались технологии: Kotlin, Google Fit API, Room Database. Приложение позволяет пользователям отслеживать свои тренировки, устанавливать цели и получать уведомления о прогрессе.'}]
    2 | Фадеева Татьяна Кузьминична | женский | Product Owner | Опытный Product Owner с 9-летним стажем в управлении продуктами и командами. Сильные навыки в аджайл-методологиях, стратегическом планировании и взаимодействии с ключевыми заинтересованными сторонами. Успешно запустила и масштабировала несколько продуктов, достигнув значительных бизнес-результатов и улучшив пользовательский опыт. | {'email': 'tatyana.fadeeva@example.com', 'phone': '8 764 180 2753', 'github': 'github.com/tatyana-fadeeva', 'linkedin': 'linkedin.com/in/tatyana-fadeeva', 'location': 'Мали'} | ['Agile и Scrum', 'Product Roadmap', 'User Story Mapping', 'Stakeholder Management', 'Data-Driven Decision Making', 'Leadership', 'Team Building', 'UX/UI Design Basics', 'Jira', 'Confluence'] | [{'company': 'Tech Solutions', 'end_date': '2023', 'job_title': 'Product Owner', 'start_date': '2018', 'achievements': ['Успешно запустила и масштабировала продукт для автоматизации бизнес-процессов, что привело к увеличению эффективности на 30% и росту выручки на 25%.', 'Разработала и внедрила стратегию улучшения пользовательского опыта, что повысило удовлетворенность клиентов на 20%.', 'Создала и поддерживала продукт-бэклог, обеспечивая четкое понимание приоритетов и целей команды.', 'Сотрудничала с ключевыми заинтересованными сторонами, включая руководство и технические команды, для выработки согласованных решений.']}, {'company': 'Innovatech', 'end_date': '2018', 'job_title': 'Product Manager', 'start_date': '2014', 'achievements': ['Управляла жизненным циклом продукта от идеи до запуска, обеспечивая своевременное выполнение всех этапов.', 'Разработала и внедрила методику оценки и анализа пользовательского поведения, что позволило оптимизировать функциональность продукта и повысить конверсию на 15%.', 'Организовала и проводила регулярные встречи с командой разработки, обеспечивая эффективное взаимодействие и выполнение спринтов.']}] | [{'degree': 'Магистр', 'details': 'Менеджмент', 'end_date': '2012', 'start_date': '2007', 'institution': 'Московский Государственный Университет'}] | ['Русский – родной', 'Английский – B2'] | ['Certified Scrum Product Owner (CSPO)', 'Google Analytics – Advanced'] | ['Путешествия', 'Фотография', 'Чтение книг по управлению продуктами'] | [{'link': 'github.com/tatyana-fadeeva/automation-project', 'name': 'Автоматизация бизнес-процессов', 'description': 'Разработка и запуск продукта для автоматизации бизнес-процессов, который повысил эффективность работы компании на 30% и увеличил выручку на 25%.'}, {'link': 'github.com/tatyana-fadeeva/ux-improvement', 'name': 'Улучшение пользовательского опыта', 'description': 'Проект по улучшению пользовательского опыта, который повысил удовлетворенность клиентов на 20% и увеличил конверсию на 15%.'}]
    3 | Горбачева Раиса Александровна | женский | Firmware Engineer | Опытный Firmware Engineer с 4 годами опыта в разработке и оптимизации встроенного программного обеспечения для различных устройств. Обладаю глубоким пониманием архитектуры микроконтроллеров и встраиваемых систем, а также сильными навыками в области C/C++ и Python. Имею успешный опыт работы в команде и управления проектами, что позволяет эффективно достигать поставленных целей. | {'email': 'raisa.gorbacheva@example.com', 'phone': '8 940 043 58 95', 'github': 'github.com/raisa-gorbacheva', 'linkedin': 'linkedin.com/in/raisa-gorbacheva', 'location': 'Индонезия'} | ['C/C++', 'Python', 'RTOS (FreeRTOS, Zephyr)', 'Microcontrollers (ARM, AVR)', 'Firmware Development', 'Debugging (JTAG, GDB)', 'Version Control (Git)', 'Agile Methodologies', 'Problem Solving', 'Team Collaboration'] | [{'company': 'Tech Innovations', 'end_date': '2023', 'job_title': 'Firmware Engineer', 'start_date': '2019', 'achievements': ['Разработала и внедрила firmware для IoT-устройств, что позволило увеличить производительность на 20% и снизить энергопотребление на 15%.', 'Успешно завершила проект по миграции legacy firmware на современные микроконтроллеры, сократив время разработки на 30%.', 'Создала и поддерживала документацию по разработке firmware, что улучшило процесс передачи знаний и сократило время наboarding новых сотрудников.']}] | [{'degree': 'Бакалавр', 'details': 'Специальность: Информатика и вычислительная техника', 'end_date': '2018', 'start_date': '2014', 'institution': 'Московский государственный университет'}] | ['Русский – родной', 'Английский – B2'] | ['Certified Firmware Developer (CFD) – 2021'] | ['Программирование микроконтроллеров', 'Путешествия', 'Фотография'] | [{'link': 'github.com/raisa-gorbacheva/iot-gateway-firmware', 'name': 'IoT Gateway Firmware', 'description': 'Разработка firmware для IoT-шлюза на базе ARM Cortex-M4. Использовались FreeRTOS, C/C++, и протоколы MQTT и CoAP. Проект позволил обеспечить надежную связь между устройствами и облачной платформой.'}, {'link': 'github.com/raisa-gorbacheva/low-power-sensor-node', 'name': 'Low-Power Sensor Node', 'description': 'Разработка firmware для низкоэнергетического датчика на базе AVR. Использовались оптимизации энергопотребления, такие как deep sleep режимы и энергоэффективные алгоритмы. Проект позволил увеличить время работы устройства от одной батареи на 50%.'}]
    4 | Маргарита Кирилловна Дорофеева | женский | DevOps Engineer | Опытный DevOps Engineer с 2 годами опыта в автоматизации инфраструктуры, оптимизации CI/CD пайплайнов и внедрении DevOps практик. Обладаю сильными навыками в работе с Kubernetes, Docker, и облачными платформами. Способна эффективно сотрудничать с командами разработки и операций, обеспечивая надежность и масштабируемость систем. | {'email': 'margarita.dorofeeva@example.com', 'phone': '8 (234) 422-6002', 'github': 'github.com/margarita-dorofeeva', 'linkedin': 'linkedin.com/in/margarita-dorofeeva', 'location': 'Эстония'} | ['Kubernetes', 'Docker', 'CI/CD (Jenkins, GitLab CI)', 'AWS', 'Terraform', 'Linux', 'Git', 'Python', 'Problem-solving', 'Teamwork'] | [{'company': 'TechSolutions', 'end_date': '2023', 'job_title': 'DevOps Engineer', 'start_date': '2021', 'achievements': ['Автоматизировала CI/CD пайплайны с использованием Jenkins, сократив время развертывания на 30%.', 'Внедрила мониторинг и логирование с помощью Prometheus и ELK Stack, улучшив видимость и управляемость инфраструктуры.', 'Настроила высокодоступную и масштабируемую инфраструктуру на AWS, снизив затраты на 20%.']}] | [{'degree': 'Бакалавр информационных технологий', 'details': 'Специализация: DevOps и облачные технологии', 'end_date': '2021', 'start_date': '2017', 'institution': 'Эстонский Технический Университет'}] | ['Русский – родной', 'Английский – B2'] | ['AWS Certified Solutions Architect – Associate', 'Google Cloud Professional DevOps Engineer'] | ['Программирование на Python', 'Путешествия', 'Фитнес'] | [{'link': 'github.com/margarita-dorofeeva/ci-cd-automation', 'name': 'Автоматизация CI/CD пайплайнов', 'description': 'Проект по автоматизации CI/CD пайплайнов с использованием Jenkins и GitLab CI. Включает скрипты для автоматического тестирования, сборки и развертывания приложений.'}, {'link': 'github.com/margarita-dorofeeva/monitoring-logging', 'name': 'Мониторинг и логирование', 'description': 'Проект по внедрению мониторинга и логирования с использованием Prometheus и ELK Stack. Включает конфигурации для сбора и анализа метрик и логов.'}]
    5 | Большакова Акулина Феликсовна | женский | Site Reliability Engineer | Опытный Site Reliability Engineer с 9-летним стажем в обеспечении высокой доступности и надежности систем. Специализируюсь на автоматизации процессов, мониторинге производительности и оптимизации инфраструктуры. Обладаю сильными навыками в области DevOps и системного администрирования, что позволяет эффективно решать сложные технические задачи и улучшать производительность систем. | {'email': 'akulina.bolshakova@example.com', 'phone': '+7 (710) 484-9177', 'github': 'github.com/akulina-bolshakova', 'linkedin': 'linkedin.com/in/akulina-bolshakova', 'location': 'Коста-Рика'} | ['DevOps', 'CI/CD', 'Kubernetes', 'Docker', 'Prometheus', 'Grafana', 'Terraform', 'AWS', 'Python', 'Linux', 'Problem-solving', 'Agile'] | [{'company': 'TechSolutions Inc.', 'end_date': '2023', 'job_title': 'Site Reliability Engineer', 'start_date': '2018', 'achievements': ['Разработала и внедрила CI/CD пайплайны, что сократило время развертывания на 40%.', 'Автоматизировала мониторинг и оповещения с использованием Prometheus и Grafana, повысив эффективность обнаружения и реагирования на инциденты на 30%.', 'Оптимизировала инфраструктуру с использованием Terraform, снизив затраты на облако на 25%.']}, {'company': 'WebTech Ltd.', 'end_date': '2018', 'job_title': 'System Administrator', 'start_date': '2014', 'achievements': ['Управление и поддержка серверной инфраструктуры на 100+ серверах, обеспечивающих бесперебойную работу критически важных систем.', 'Разработка и внедрение политик безопасности, что снизило количество инцидентов на 50%.', 'Внедрение контейнеризации с использованием Docker, улучшив масштабируемость и производительность приложений.']}] | [{'degree': 'Бакалавр информационных технологий', 'details': 'Специализация: Системное администрирование и сетевые технологии', 'end_date': '2013', 'start_date': '2009', 'institution': 'Национальный университет информационных технологий'}] | ['Русский – родной', 'Английский – C1'] | ['AWS Certified DevOps Engineer – Professional', 'Google Cloud Professional Cloud Architect'] | ['Путешествия', 'Программирование на Python', 'Фотография'] | [{'link': 'github.com/akulina-bolshakova/monitoring-automation', 'name': 'Автоматизация мониторинга и оповещений', 'description': 'Разработка и внедрение системы мониторинга с использованием Prometheus и Grafana для улучшения обнаружения и реагирования на инциденты.'}, {'link': 'github.com/akulina-bolshakova/terraform-optimization', 'name': 'Оптимизация инфраструктуры с использованием Terraform', 'description': 'Проект по оптимизации инфраструктуры с использованием Terraform, снизивший затраты на облако на 25%.'}]

    Examples:
        >>> sql_engine(\'''
            SELECT id, name, title
            FROM resumes
            WHERE 'Kubernetes' = ANY(skills)
            ORDER BY id
            LIMIT 5;
        \''')
        "[ (4, 'Маргарита Кирилловна Дорофеева', 'DevOps Engineer'), ... ]"

        >>> sql_engine(\'''
            UPDATE resumes
            SET title = 'Mobile Developer'
            WHERE id = 1;
        \''')
        "Query executed successfully, but no results to fetch."

    Important:
        • Use provided schema and select only available columns
        • Never pass raw user input directly into *query*; always parameterize
          to avoid SQL injection.
        • Avoid requesting more than 1 000 rows per call to keep responses
          manageable for the language model.


    Examples:
        >>> sql_engine(\"""
            SELECT id, name, title
            FROM resumes
            WHERE 'Kubernetes' = ANY(skills)
            ORDER BY id
            LIMIT 5;
        \""")
        "[ (4, 'Маргарита Кирилловна Дорофеева', 'DevOps Engineer'), ... ]"

    Important:
        • Never pass raw user input directly into *query*; always parameterize
          to avoid SQL injection.
        • Avoid requesting more than 1 000 rows per call to keep responses
          manageable for the language model.

    """  # noqa: E501
    output = ""
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    cursor.execute(query)

    try:
        output = cursor.fetchall()
    except psycopg2.ProgrammingError:
        output = "Query executed successfully, but no results to fetch."

    conn.commit()
    conn.close()
    return output


openai_provider = OpenAIProvider(
    openai_client=AsyncOpenAI(
        base_url=os.getenv("LLM_API_URL"),
        api_key=os.getenv("LLM_API_TOKEN"),
    )
)
openai_model = OpenAIModel(os.getenv("LLM_API_MODEL"), provider=openai_provider)


sql_tool = Tool(
    function=sql_engine,
    takes_ctx=False,
)

pydantic_ai_agent = Agent(
    openai_model,
    system_prompt="""
    You are an SQL analyst. For that you are provided with a set of tools.
    Always detect the language of the user's query and respond in the same language.\n
    You must use the `sql_tool` tool to answer queries about resumes.\n
    NEVER make up data — always rely on real SQL results.\n
    Use short, factual answers based strictly on the query results.\n
    Casual conversation is allowed, but data answers must come from the database only.
    """,
    tools=[sql_tool],
)
