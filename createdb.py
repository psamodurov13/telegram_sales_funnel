from config import *
from datetime import date
from db import *
from posts import posts
query = f'''
create table if not exists tags(
    id integer primary key AUTOINCREMENT,
    name text NOT NULL
);
create table if not exists users(
    id integer primary key AUTOINCREMENT,
    telegram_id integer UNIQUE,
    first_name text,
    last_name text,
    username text,
    created_at datetime,
    current_step integer
);
create table if not exists users_tags(
    user_id integer,
    tag_id integer,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (tag_id) REFERENCES tags (id),
    PRIMARY KEY (user_id, tag_id)
);
create table if not exists post_types(
    id integer primary key AUTOINCREMENT,
    name text NOT NULL
);
create table if not exists actions(
    id integer primary key AUTOINCREMENT,
    name text
);
create table if not exists buttons(
    id integer primary key AUTOINCREMENT,
    button_text text,
    button_url text,
    next_post integer,
    FOREIGN KEY (next_post) REFERENCES posts (id)
);
create table if not exists buttons_actions(
    button_id integer,
    action_id integer,
    FOREIGN KEY (button_id) REFERENCES buttons (id),
    FOREIGN KEY (action_id) REFERENCES actions (id),
    PRIMARY KEY (button_id, action_id)
);
create table if not exists posts(
    id integer primary key AUTOINCREMENT,
    text text,
    photo text,
    audio text,
    video text,
    count integer,
    timer integer,
    time datetime,
    default_next integer
);
create table if not exists posts_add_tags(
    post_id integer,
    tag_id integer,
    FOREIGN KEY (post_id) REFERENCES posts (id),
    FOREIGN KEY (tag_id) REFERENCES tags (id),
    PRIMARY KEY (post_id, tag_id)
);
create table if not exists posts_buttons(
    button_id integer,
    post_id integer,
    FOREIGN KEY (button_id) REFERENCES buttons (id),
    FOREIGN KEY (post_id) REFERENCES posts (id),
    PRIMARY KEY (button_id, post_id)
);
create table if not exists posts_post_types(
    post_id integer,
    post_type_id integer,
    FOREIGN KEY (post_id) REFERENCES posts (id),
    FOREIGN KEY (post_type_id) REFERENCES post_types (id),
    PRIMARY KEY (post_id, post_type_id)
);
    
insert into actions(name) values ('Ссылка');
insert into actions(name) values ('Следующий пост');

insert into tags(name) values 
('Вступил в прогрев'),
('Забрал подарок');

insert into post_types(name) values 
('Элемент воронки'),
('Шаблон ответа');
'''


def get_query_for_posts():
    for post in posts:
        posts_values = {k: v for k, v in post.items() if v and k not in ['add_tags', 'buttons', 'post_type']}
        logger.info(f'POST VALUES - {posts_values}')
        insert('posts', posts_values)
        # Пост добавлен
        fetched_post_types = fetchall('post_types', ['id'], f'name = "{post["post_type"]}"')
        post_type_id = fetched_post_types[0]['id']
        fetched_post = fetchall('posts', ['id'], f'count = {post["count"]}')
        logger.info(f'FETCHED POST - {fetched_post}')
        post_id = fetched_post[0]['id']
        logger.info(f'FETCHED POST TYPES {fetched_post_types} / {post_type_id}')
        posts_post_types_values = {
            'post_id': post_id,
            'post_type_id': post_type_id
        }
        logger.info(f'POST/POST_TYPE VALUES - {posts_values}')
        insert('posts_post_types', posts_post_types_values)
        # Связь поста с типом поста добавлена
        if post['buttons']:
            for button in post['buttons']:
                button_values = {
                    'button_text': button.get('button_text', None),
                    'button_url': button.get('button_url', None),
                    'next_post': button.get('next_post', None)
                }
                logger.info(f'BUTTON VALUES - {button_values}')
                insert('buttons', button_values)
                fetched_actions = fetchall('actions', ['id'], f'name = "{button["action"]}"')
                action_id = fetched_actions[0]['id']
                button_id = fetchall('buttons', ['id'])[-1]['id']
                buttons_actions_values = {
                    'button_id': button_id,
                    'action_id': action_id
                }
                logger.info(f'BUTTONS ACTIONS VALUES - {buttons_actions_values}')
                insert('buttons_actions', buttons_actions_values)
                posts_buttons_values = {
                    'post_id': post_id,
                    'button_id': button_id
                }
                logger.info(f'POST BUTTONS VALUES - {posts_buttons_values}')
                insert('posts_buttons', posts_buttons_values)
        if post['add_tags']:
            for tag in post['add_tags']:
                tag_id = fetchall('tags', ['id'], f'name = "{tag}"')[0]['id']
                posts_add_tags = {
                    'post_id': post_id,
                    'tag_id': tag_id
                }
                insert('posts_add_tags', posts_add_tags)

