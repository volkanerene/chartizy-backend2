import json
from typing import Dict, Any, Optional
from openai import OpenAI
from ..config import get_settings


class OpenAIService:
    """Service for OpenAI chart generation."""
    
    _client: Optional[OpenAI] = None
    
    @classmethod
    def get_client(cls) -> OpenAI:
        """Get or create OpenAI client."""
        if cls._client is None:
            settings = get_settings()
            cls._client = OpenAI(api_key=settings.openai_api_key)
        return cls._client
    
    @classmethod
    def build_chart_prompt(cls, chart_type: str, data: Dict[str, Any]) -> str:
        """Build the prompt for chart generation."""
        # Special handling for advanced chart types
        chart_instructions = {
            "waterfall": "Create a waterfall chart showing cumulative changes. Use a bar chart with stacked segments where each bar represents a change from the previous value. Show positive changes in one color and negative in another.",
            "funnel": "Create a funnel chart showing conversion stages. Use a bar chart with decreasing widths, or a custom funnel visualization with stages labeled clearly.",
            "sankey": "Create a Sankey diagram showing flow between nodes. Use a custom visualization with paths connecting source to target nodes. Include node labels and flow values.",
            "gantt": "Create a Gantt chart showing project timeline. Use a bar chart with horizontal bars representing time periods. Include task names and date ranges.",
            "3d": "Create a 3D visualization using Plotly.js. Include proper camera controls, lighting, and interactive rotation. Use Plotly's Scatter3d or Surface3d.",
            "3d-surface": "Create a 3D surface plot using Plotly.js Surface3d. Show data as a 3D surface with color mapping.",
            "3d-bar": "Create a 3D bar chart using Plotly.js. Show bars in 3D space with proper depth and perspective.",
            "heatmap": "Create a heatmap showing intensity values. Use a 2D grid with color gradients representing values. Include axis labels and color scale.",
            "treemap": "Create a treemap showing hierarchical data. Use nested rectangles sized by value. Include labels and color coding.",
            "sunburst": "Create a sunburst chart showing hierarchical data in circular form. Use nested arcs with proper sizing and coloring.",
            "candlestick": "Create a candlestick chart for financial data. Show open, high, low, close values with proper candlestick visualization.",
        }
        
        special_instruction = chart_instructions.get(chart_type.lower(), "")
        instruction_text = f"\n{special_instruction}\n" if special_instruction else ""
        
        # Determine library based on chart type
        if chart_type.lower() in ["3d", "3d-surface", "3d-bar"]:
            library_note = "Use Plotly.js for 3D rendering. Import Plot from 'react-plotly.js'."
        elif chart_type.lower() in ["sankey", "treemap", "sunburst"]:
            library_note = "Use D3.js or a custom React component for this visualization. Include all necessary imports."
        else:
            library_note = "Use Chart.js with react-chartjs-2. Import from 'react-chartjs-2' and 'chart.js'."
        
        return f"""You are an expert data visualization designer specializing in Chart.js, Plotly.js, and D3.js.

Based on the provided data, generate a complete chart configuration for a {chart_type} chart.
{instruction_text}
{library_note}

DATA:
{json.dumps(data, indent=2)}

REQUIREMENTS:
1. Analyze the data structure and create appropriate labels and datasets
2. Use beautiful, modern colors (soft pastels: #8B5CF6, #06B6D4, #10B981, #F59E0B, #EF4444, #EC4899)
3. Include proper chart options for responsiveness and aesthetics
4. Generate clean, production-ready code
5. For 3D charts, include camera controls and interactive features
6. For advanced charts (Sankey, Treemap, Sunburst), use appropriate libraries

Return ONLY valid JSON in this exact format (no markdown, no extra text):
{{
    "chartConfig": {{
        "type": "{chart_type.lower()}",
        "data": {{
            "labels": [...],
            "datasets": [...]
        }},
        "options": {{...}}
    }},
    "jsx": "<complete React component with all necessary imports>",
    "description": "<brief description of what the chart shows>"
}}

IMPORTANT:
- The chartConfig must be a valid configuration object for the chosen library
- The jsx must be a complete, self-contained React functional component
- Include all necessary imports in the jsx (react-chartjs-2, plotly.js, d3, etc.)
- Use modern React patterns (hooks, functional components)
- Make the chart responsive and visually appealing
- For 3D charts, ensure proper Plotly.js setup with camera controls"""

    @classmethod
    async def generate_chart(
        cls,
        chart_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate chart configuration using GPT-4 Turbo."""
        client = cls.get_client()
        prompt = cls.build_chart_prompt(chart_type, data)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data visualization expert. Always respond with valid JSON only, no markdown formatting or extra text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                chartConfig = result.get("chartConfig", {})
                
                # Extract title from data if provided, or use description as title
                data = data if isinstance(data, dict) else {}
                title = data.get("title") or result.get("description", "Chart")
                
                # Add title to chartConfig options if not already present
                if "options" not in chartConfig:
                    chartConfig["options"] = {}
                if "title" not in chartConfig["options"]:
                    chartConfig["options"]["title"] = {
                        "display": True,
                        "text": title
                    }
                
                # Also add title to data for easy access
                if "data" in chartConfig and isinstance(chartConfig["data"], dict):
                    chartConfig["data"]["title"] = title
                
                return {
                    "success": True,
                    "chartConfig": chartConfig,
                    "jsx": result.get("jsx", ""),
                    "description": result.get("description", ""),
                    "svg": result.get("svg")
                }
            
            return {
                "success": False,
                "error": "Empty response from OpenAI"
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse response: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @classmethod
    def get_chart_type_from_template(cls, template_name: str) -> str:
        """Map template name to Chart.js chart type."""
        mapping = {
            "line": "line",
            "bar": "bar",
            "stacked bar": "bar",
            "stacked-bar": "bar",
            "area": "line",
            "pie": "pie",
            "donut": "doughnut",
            "doughnut": "doughnut",
            "radar": "radar",
            "bubble": "bubble",
            "scatter": "scatter",
            "polar": "polarArea",
            "polar area": "polarArea",
            "waterfall": "waterfall",
            "funnel": "funnel",
            "sankey": "sankey",
            "gantt": "gantt",
            "heatmap": "heatmap",
            "treemap": "treemap",
            "sunburst": "sunburst",
            "candlestick": "candlestick",
            "3d": "3d",
            "3d-surface": "3d",
            "3d-bar": "3d",
        }
        return mapping.get(template_name.lower(), "bar")

    @classmethod
    async def analyze_chart_prompt(cls, prompt: str) -> Dict[str, Any]:
        """
        Analyze a natural language prompt and generate appropriate chart data.
        Uses GPT-4 to understand context and create meaningful data.
        """
        client = cls.get_client()
        
        system_prompt = """You are an expert data analyst and visualization specialist.
Your task is to analyze user prompts (in ANY language) and generate appropriate chart data.

IMPORTANT RULES:
1. Understand the user's intent, even if vague or creative
2. Generate realistic, meaningful data that matches the description
3. If the user mentions specific values or time periods, use them
4. If the user describes a trend (increasing, decreasing), reflect that in the data
5. Choose the most appropriate chart type based on the data nature
6. Respond in the SAME LANGUAGE as the user's prompt for title and description

You must respond with ONLY valid JSON in this exact format:
{
    "success": true,
    "labels": ["Label1", "Label2", ...],
    "values": [number1, number2, ...],
    "title": "Chart title in user's language",
    "description": "Brief description in user's language",
    "suggested_charts": [
        {"chart_type": "line", "confidence": 95, "reason": "Reason in user's language"},
        {"chart_type": "bar", "confidence": 70, "reason": "Reason in user's language"}
    ],
    "data_interpretation": "Explanation of how you interpreted the prompt"
}

Chart types available: line, bar, pie, doughnut, area, scatter, radar, stacked-bar, waterfall, funnel, sankey, gantt, heatmap, treemap, sunburst, candlestick, 3d, 3d-surface, 3d-bar"""

        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this prompt and generate chart data:\n\n{prompt}"}
                ],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                return {
                    "success": True,
                    "labels": result.get("labels", []),
                    "values": result.get("values", []),
                    "title": result.get("title", ""),
                    "description": result.get("description", ""),
                    "suggested_charts": result.get("suggested_charts", []),
                    "data_interpretation": result.get("data_interpretation", "")
                }
            
            return {"success": False, "error": "Empty response"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    async def generate_chart_data(
        cls,
        description: str,
        data_points: int = 6,
        chart_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate sample data based on a description.
        """
        client = cls.get_client()
        
        chart_hint = f"for a {chart_type} chart" if chart_type else ""
        
        system_prompt = f"""Generate realistic chart data {chart_hint} based on the description.
Return ONLY valid JSON:
{{
    "labels": ["Label1", "Label2", ...],  // {data_points} labels
    "values": [num1, num2, ...],  // {data_points} numeric values
    "title": "Descriptive title",
    "suggested_type": "line|bar|pie|doughnut|area"
}}

Make the data realistic and match the description's intent."""

        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": description}
                ],
                temperature=0.4,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            
            return {"error": "Empty response"}
            
        except Exception as e:
            return {"error": str(e)}

