
class API_STORE:
    
    access_token = None
    loan_guid = None
    
    def set_access_token(self, access_token):
        self.access_token = access_token

    def get_access_token(self):
        return self.access_token
    
    def set_loan_guid(self, loan_guid):
        self.loan_guid = loan_guid

    def get_loan_guid(self):
        return self.loan_guid
        
        