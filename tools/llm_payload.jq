# Read raw text files and build the JSON payload
{
  "model": env.LLM_MODEL,
  "temperature": (env.LLM_TEMP | tonumber),
  "messages": [
    {
      "role": "system",
      "content": ($system)
    },
    {
      "role": "user",
      "content": ($user)
    }
  ]
}