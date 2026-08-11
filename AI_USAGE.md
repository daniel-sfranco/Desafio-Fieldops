# Documentação sobre o uso de IA no projeto Fieldops

## Ferramentas utilizadas
Para esse projeto, foi utilizado como auxiliar de desenvolvimento o Antigravity, aplicação desktop fornecido pelo Google, contando com os modelos Gemini, em especial o modelo Gemini 3.5 Flash.

## Geração automática e revisão manual
A inteligência artificial foi utilizada neste projeto com o intuito de acelerar seu desenvolvimento, economizando tempo ao executar tarefas trabalhosas como ajuste visual dos elementos com HTML e CSS, além de me guiar quanto aos requisitos técnicos e de lógica de negócio ao desenvolver a aplicação.
A IA foi utilizada para gerar HTML e CSS sem revisão manual, sendo avaliada apenas através do teste na url da plataforma e avaliação da usabilidade do aplicativo, além do aspecto estético. Também foram gerados sem revisão direta os testes unitários, envolvendo diversos escopos no backend.
Schemas e modelos também foram gerados, no backend, sendo que estes foram criados no início do desenvolvimento da aplicação, e ao longo do desenvolvimento das rotas foram ajustados conforme necessidade.
Algumas implementações lógicas no frontend foram geradas pela inteligência artificial, mas implementadas por mim. Isso foi feito com o intuito de aprender e me desenvolver no framework React, utilizado no projeto, pois não tenho muita experiência no mesmo e desejo entender melhor seu funcionamento.
Por último, mas não menos importante, a inteligência artificial foi utilizada para o meu entendimento do escopo do projeto. Eu submeti o arquivo com as diretrizes para ela e pedi por um detalhamento quanto a esses requisitos, fazendo por mim mesmo um resumo e tirando as dúvidas que surgiam.

## Decisão técnica com discordância
Como as decisões arquiteturais e a implementação das rotas e regras de negócio foram feitas de forma autônoma por mim, não houve um cenário de conflito direto com sugestões automáticas. 
No entanto, um cuidado técnico deliberado na minha implementação foi **não adotar o padrão genérico** comumente gerado por assistentes de IA (que costumam sugerir travas de concorrência ou exigência de `version` em qualquer atualização de dados). Em vez disso, projetei a rota `PATCH /work-orders/:id` para disparar a validação de concorrência otimista (`FLX_CONCURRENT_UPDATE`) estritamente quando há tentativa de transição de `status`, mantendo a rota flexível para alterações parciais de outros campos conforme o escopo do edital.

## Partes escritas sem assistente
As principais partes escritas sem assistente foram boa parte das rotas, assegurando a maior parte das regras de negócio especificadas através delas. A implementação de CI, configuração do banco de dados e dockerização também foram feitos de forma autônoma, assim como a configuração inicial dos projetos, tanto do projeto React como o início do FastAPI. 

## Limitações que permanecem na entrega
O webhook poderia contar com uma fila assíncrona para envio das requisições. Em caso de falha na API, a tarefa em memória (inserida ali utilizando o `BachgroundTasks` nativo do FastAPI) é perdida. A fila assíncrona usaria um Message Broker como Redis ou RabbitMQ e um orquestrador de tarefas em segundo plano, como Celery ou ARQ / RQ no Python.
