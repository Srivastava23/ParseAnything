from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, BaseModel
from typing import Optional

class CoreOptions(BaseModel):
    dpi: int = 200
    workers: int = 4
    confidence_threshold: float = 0.6
    enable_cloud_fallbacks: bool = False

class BackendOptions(BaseModel):
    ocr: str = "rapidocr"
    layout: str = "docling"
    vlm: str = "stub_vlm"

class CostOptions(BaseModel):
    ocr_cost_per_page: float = 0.0015
    vlm_cost_per_page: float = 0.005

class Options(BaseSettings):
    core: CoreOptions = Field(default_factory=CoreOptions)
    backends: BackendOptions = Field(default_factory=BackendOptions)
    costs: CostOptions = Field(default_factory=CostOptions)
    
    # Backwards compatibility properties
    @property
    def dpi(self): return self.core.dpi
    @property
    def workers(self): return self.core.workers
    @property
    def confidence_threshold(self): return self.core.confidence_threshold
    @property
    def enable_cloud_fallbacks(self): return self.core.enable_cloud_fallbacks
    @property
    def ocr_backend(self): return self.backends.ocr
    @property
    def layout_backend(self): return self.backends.layout
    @property
    def vlm_backend(self): return self.backends.vlm
    @property
    def ocr_cost_per_page(self): return self.costs.ocr_cost_per_page
    @property
    def vlm_cost_per_page(self): return self.costs.vlm_cost_per_page

    model_config = SettingsConfigDict(yaml_file='config.yaml', yaml_file_encoding='utf-8', extra='ignore')

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        from pydantic_settings import YamlConfigSettingsSource
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls),
        )
