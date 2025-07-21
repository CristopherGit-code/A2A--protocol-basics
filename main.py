import oci,logging
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference import models
from config import Settings
import ast

logger = logging.getLogger(name=f'File.{__name__}----------->')

# General variables --------------------------
PREAMBLE = 'Answer in maximum, 200 words'
MESSAGE = ''

class Client:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.endpoint = self.settings.oci_client.endpoint
        self.config = oci.config.from_file(
            self.settings.oci_client.config_path, 
            self.settings.oci_client.configProfile)
        self.endpoint = self.settings.oci_client.endpoint
        self.client = GenerativeAiInferenceClient(
            config=self.config, 
            service_endpoint=self.endpoint, 
            retry_strategy=oci.retry.NoneRetryStrategy(), 
            timeout=(10,240))
        
        self.chat_detail = models.ChatDetails()
        self.chat_detail.serving_mode = models.OnDemandServingMode(
            model_id=self.settings.oci_client.model_id)
        self.chat_detail.compartment_id = self.settings.oci_client.compartiment

        self.message_db = {}

        self.chat_request = models.CohereChatRequest()
        self.chat_request.preamble_override = PREAMBLE # user
        self.chat_request.message = MESSAGE #user
        self.chat_request.max_tokens = self.settings.oci_client.max_tokens
        self.chat_request.temperature = self.settings.oci_client.temperature
        self.chat_request.frequency_penalty = self.settings.oci_client.freq_penalty
        self.chat_request.top_p = self.settings.oci_client.top_p
        self.chat_request.top_k = self.settings.oci_client.top_k  
        
    def _get_chat_details(self):
        self.chat_detail.chat_request = self._get_chat_request()

        return self.chat_detail
    
    # Chat parameters
    def _get_chat_request(self):
        return self.chat_request
    
    def _set_chat_request(self, prompt, instructions, user_id):
        self.chat_request.preamble_override = PREAMBLE + instructions # user (keep 200 word limit)
        self.chat_request.message = prompt #user
        self.chat_request.chat_history = self.message_db[user_id]

    def _get_user_chat_history(self,user_id):
        try:
            return self.message_db[user_id]
        except KeyError as k:
            return []

    def _manage_chat_history(self,user_id,message):
        message_history = self._get_user_chat_history(user_id)
        if not message_history:
            self.message_db[user_id] = []
        self.message_db[user_id].append(message)
        
    
    def _call_client(self,u_prompt, user_id, sys_instructions=''):
        self._manage_chat_history(user_id,models.CohereUserMessage(message=u_prompt))
        try:
            self._set_chat_request(u_prompt, sys_instructions, user_id)
            client_config = self._get_chat_details()
            chat_response = self.client.chat(client_config)
            generated_response = chat_response.data.chat_response.text
        except oci.exceptions.ServiceError as s:
            logger.debug(s)
            generated_response = f'Error in fetching the message: {s.message}'
        except Exception as e:
            logger.debug(e)
            generated_response = f'General internal error: {e}'
        self._manage_chat_history(user_id,models.CohereChatBotMessage(message=generated_response))
        #logger.debug(self.message_db[user_id])
        return generated_response
    
    def provide_analysis(self, query:str, u_instructions:str, user_id:str) -> str:
        prompt = self.settings.analysis_prompt + query
        instructions = self.settings.analysis_instructions + u_instructions
        response = self._call_client(prompt,user_id,instructions)
        return response

    def filter_files(self, query:str) -> list:
        prompt = self.settings.filter_prompt + query
        instructions = self.settings.filter_instructions
        response = self._call_client(prompt, instructions,'FILTER')
        try:
            r_dict = ast.literal_eval(response)
        except Exception as e:
            r_dict = [2010,None,None,None]
        return r_dict
    
    def reset_chat(self,user_id):
        self.message_db[user_id] = []

def main():
    settings = Settings("config.yaml")
    llm = Client(settings)
    while True:
        prompt = input('User: ')
        ans = llm._call_client(prompt,'WER')
        print(ans)
    
if __name__ == "__main__":
    main()