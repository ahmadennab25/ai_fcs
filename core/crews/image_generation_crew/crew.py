"""
Agent 2 — Image Generation Crew.

Takes the image prompt written by Agent 1, refines it for Facebook, calls
the image generation tool, and returns the reference of the generated image.
"""
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from core.tools import ImageGenerationTool, basic_llm


@CrewBase
class ImageGenerationCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def art_director(self) -> Agent:
        return Agent(
            config=self.agents_config["art_director"],
            verbose=True,
            llm=basic_llm,
            tools=[ImageGenerationTool()],
        )

    @task
    def generate_image_task(self) -> Task:
        return Task(
            config=self.tasks_config["generate_image_task"],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
