import os
import openai
from git import Repo
from pathlib import Path
import shutil
import requests
from bs4 import BeautifulSoup as Soup

PATH_TO_BLOG_REPO = Path('/Users/jjosey/Python/openai_tutorials/automatic_blog_post_creator/.git')
PATH_TO_BLOG = PATH_TO_BLOG_REPO.parent
PATH_TO_BLOG_CONTENT = PATH_TO_BLOG / 'content'
PATH_TO_BLOG_CONTENT.mkdir(exist_ok=True, parents=True)

openai.api_key = os.getenv("OPENAI_SECRET_KEY")


def update_blog(commit_message ='Updates blog'):
    ## Git Python
    repo = Repo(PATH_TO_BLOG_REPO)
    repo.git.add(update=True)
    repo.index.commit(commit_message)
    origin = repo.remote(name='origin')
    origin.push()


def create_new_blog(title,content, cover_image):
    cover_image = Path(cover_image)

    files = len(list(PATH_TO_BLOG_CONTENT.glob('*.html')))
    new_title = f"{files+1}.html"
    path_to_new_content = PATH_TO_BLOG_CONTENT / new_title

    shutil.copy(cover_image, PATH_TO_BLOG_CONTENT)

    if not os.path.exists(path_to_new_content):
        with open(path_to_new_content, 'w') as f:
            f.write("<!DOCTYPE html>\n")
            f.write("<html>\n")
            f.write("<head>\n")
            f.write(f"<title> {title} </title>\n")
            f.write("</head>\n")
            f.write("<body>\n")
            f.write(f"<img src='{cover_image.name}' alt='Cover Image'> <br />\n")
            f.write(f"<h1> {title} </h1>\n")
            f.write(content.replace("\n", "<br/>\n"))
            f.write("</body>\n")
            f.write("</html>\n")
        return path_to_new_content
    else:
        raise FileExistsError("File already exisits,  please check again your name!")


def check_for_duplicate_links(path_to_new_content, links):
    urls = [str(link.get("href")) for link in links]
    content_path = str(Path(*path_to_new_content.parts[-2:]))
    return content_path in urls

def write_to_index(path_to_new_content):
    with open(PATH_TO_BLOG / 'index.html') as index:
        soup =Soup(index.read(), 'html.parser')

    links = soup.find_all('a')
    last_link = links[-1]
    if check_for_duplicate_links(path_to_new_content, links):
        raise ValueError("Link already exisits")
    else:
        link_to_new_blog = soup.new_tag('a', href=Path(*path_to_new_content.parts[-2:]))
        link_to_new_blog.string = f"blog {path_to_new_content.stem.split('.')[0]}"
        last_link.insert_after(link_to_new_blog)

    with open(PATH_TO_BLOG / 'index.html', 'w') as f:
        f.write(str(soup.prettify(formatter='html')))


def create_prompt(title):
    prompt = f"""
    Biography:
    My name is Jeff and i am Python instructor for coding. Who writes in the voice of Hunter s Thompson in a comedic tone.

    Blog:
    Title: {title}
    tags: python, openai, blog
    Summary: I write about the future of AI and Python

    full_text:: """.format(title)
    return prompt

def dalle2_prompt(title):
    prompt = f" an oil painting depicting {title} in the style of salvador dali"
    return prompt


def save_image(image_url, file_name):
    image_res = requests.get(image_url, stream=True)
    if image_res.status_code == 200:
        with open(file_name, 'wb') as f:
          shutil.copyfileobj(image_res.raw, f)
    else:
        print("Couldn't save image")
    return image_res.status_code


title = 'The future of AI and Python'
response = openai.Completion.create(
  engine="text-davinci-003",
  prompt=create_prompt(title),
  temperature=0.7,
  max_tokens=1000)

blog_content = response['choices'][0]['text']
image_prompt = dalle2_prompt(title)
image_response = openai.Image.create(prompt=image_prompt, n=1, size="1024x1024")
image_url = image_response['data'][0]['url']
save_image(image_url, 'title3.png')
#print(image_url)
#print(blog_content)



path_to_new_content = create_new_blog(title, blog_content, 'title3.png')
write_to_index(path_to_new_content)
update_blog(commit_message = 'Added new blog post')

