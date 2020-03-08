%include('header.tpl', title='Settings')
% s = settings
% ov = str('This setting is currently overriden by the variable {} in your environment')

<h1>Settings</h1>

<table class="no-border left-align">
    <tr>
        <td></td>
        <td><b>Version:</b></td>
        <td>{{s['version']}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_SERVER_PROFILE')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Active profile:</b></td>
        <td>{{s['name']}}</td>
    </tr>
    <tr>
        <td></td>
        <td><b>Default format:</b></td>
        <td><span title="{{s['value']}}">{{s['label']}}</span></td>
    </tr>
    <tr>
        % var_name = str('YDL_OUTPUT_TEMPLATE')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Output Template:</b></td>
        <td><code>{{s[var_name]}}</code></td>
    </tr>
    <tr>
        % var_name = str('YDL_WRITE_SUB')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Write subtitles:</b></td>
        <td>{{bool(s[var_name])}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_ALL_SUBS')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Write all subtitles:</b></td>
        <td>{{bool(s[var_name])}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_IGNORE_ERRORS')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Ignore errors:</b></td>
        <td>{{bool(s[var_name])}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_CONTINUE_DL')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Continue downloads:</b></td>
        <td>{{bool(s[var_name])}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_NO_OVERWRITES')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>No overwrites:</b></td>
        <td>{{bool(s[var_name])}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_ADD_METADATA')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Add metadata:</b></td>
        <td>{{bool(s[var_name])}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_WRITE_DESCRIPTION')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Write description:</b></td>
        <td>{{bool(s[var_name])}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_WRITE_INFO_JSON')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Write info.json:</b></td>
        <td>{{bool(s[var_name])}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_WRITE_ANNOTATIONS')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Write annotations:</b></td>
        <td>{{bool(s[var_name])}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_WRITE_THUMBNAIL')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Write thumbnail:</b></td>
        <td>{{bool(s[var_name])}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_EMBED_THUMBNAIL')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Embed thumbnail:</b></td>
        <td>{{bool(s[var_name])}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_SUB_FORMAT')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Subtitle format:</b></td>
        <td>{{s[var_name]}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_EMBED_SUBS')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Embed subtitles:</b></td>
        <td>{{bool(s[var_name])}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_MERGE_OUTPUT_FORMAT')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Merged format:</b></td>
        <td>{{s[var_name]}}</td>
    </tr>
    <tr>
        % var_name = str('YDL_RECODE_VIDEO')
        <td>
            %if (var_name in overrides):
            <span class="icon" title="{{ov.format(var_name)}}">🔒</span></td>
            %end
        </td>
        <td><b>Recode video:</b></td>
        <td>{{bool(s[var_name])}}</td>
    </tr>
</table>

%include('footer.tpl')
