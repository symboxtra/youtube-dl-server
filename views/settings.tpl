%include('header.tpl', title='Settings')
% s = settings
% ov = str('This setting is currently overriden by the variable {} in your environment')

<h1>Settings</h1>

<table class="no-border left-align">
    <tr>
        <td></td>
        <td><b>Version:</b></td>
        <td>
            <code>{{s['version']}}</code>
        </td>
    </tr>
    <tr>
        % var_name = str('YDL_SERVER_PROFILE')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Active profile:</b></td>
        <td>
            <code>{{s['name']}}</code>
        </td>
    </tr>
    <tr>
        <td></td>
        <td><b>Default format:</b></td>
        <td title="{{s['value']}}">
            <code>{{s['label']}}</code>
        </td>
    </tr>

    %for opt in ydl_options:
    <tr>
        <td>
            %if (opt['env_name'] in overrides):
            <span class="icon" title="{{ov.format(opt['env_name'])}}">🔒</span></td>
            %end
        </td>
        <td title="{{opt['help_text']}}">
            <b>{{opt['plain_name']}}:</b>
        </td>
        <td>
            <code>{{s[opt['env_name']]}}</code>
        </td>
    </tr>
    %end
</table>

%include('footer.tpl')
