"""
Agent 1 — Post Writer Crew.

Takes a campaign brief and a topic and writes a ready-to-publish Facebook
post (caption, hashtags, call to action) plus a vivid image prompt for
Agent 2 to render.
"""
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from core.tools import basic_llm


@CrewBase
class PostWriterCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def facebook_copywriter(self) -> Agent:
        return Agent(
            config=self.agents_config["facebook_copywriter"],
            verbose=True,
            llm=basic_llm,
        )

    @task
    def write_post_task(self) -> Task:
        return Task(
            config=self.tasks_config["write_post_task"],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
